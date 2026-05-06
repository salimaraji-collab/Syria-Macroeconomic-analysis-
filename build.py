#!/usr/bin/env python3
"""
build.py — Syria Macroeconomic Brief data pipeline
====================================================
Reads raw data files from data/raw/ and produces data/processed.json,
which the dashboard (index.html) loads at runtime via fetch().

Run this whenever you update the raw data files. The dashboard will
automatically reflect the new analysis on the next page load.

Usage:
    pip install pandas openpyxl
    python build.py

The script can also be triggered automatically on every push to GitHub via
the workflow at .github/workflows/build.yml — no manual run needed.

Expected files in data/raw/ (CSV or XLSX both supported):
    wfp_prices.csv               WFP VAM food prices, wages, exchange rate
    port_incoming_tartus.csv     Daily incoming vessel DWT, Tartus
    port_incoming_latakia.csv    Daily incoming vessel DWT, Latakia
    port_outgoing_tartus.csv     Daily outgoing vessel DWT, Tartus
    port_outgoing_latakia.csv    Daily outgoing vessel DWT, Latakia
    remote_sensing.csv           Monthly nightlights radiance + NDVI

Configuration constants below (BASKET_FULL, ANCHOR_DATE, etc.) define the
analytical choices. Change them if you want to anchor on a different month
or use a different basket composition.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("Missing dependency. Run: pip install pandas openpyxl")

# ============================================================================
# CONFIGURATION — adjust as needed
# ============================================================================
RAW_DIR     = Path("data/raw")
OUTPUT_FILE = Path("data/processed.json")

# Comparison anchors for year-on-year analysis
ANCHOR_PERIOD     = "2026-04"   # the "as of" month
COMPARISON_PERIOD = "2025-04"   # YoY base

# Pre-transition reference (for context-only KPIs, not used for headline YoY)
PRE_START = "2024-01"
PRE_END   = "2024-11"

# Transition date
TRANSITION_DATE = "2024-12-08"

# Working days assumption for converting daily wage to monthly USD
WORKING_DAYS_PER_MONTH = 22

# WFP food basket (13 items)
BASKET_FULL = [
    "Bread (bakery)", "Rice", "Wheat flour", "Sugar", "Oil", "Potatoes",
    "Eggs", "Lentils", "Bulgur", "Chickpeas", "Onions", "Tomatoes",
    "Meat (chicken, legs)",
]

# Port-call ship-type columns
SHIP_COLS = ["Container", "Dry Bulk", "General Cargo", "Roll-on/roll-off", "Tanker"]


# ============================================================================
# HELPERS
# ============================================================================
def load_table(stem: str) -> pd.DataFrame:
    """Load a CSV or XLSX from RAW_DIR by stem (filename without extension)."""
    for ext in [".csv", ".xlsx", ".xls"]:
        path = RAW_DIR / f"{stem}{ext}"
        if path.exists():
            print(f"  → reading {path.name}")
            if ext == ".csv":
                return pd.read_csv(path, low_memory=False)
            return pd.read_excel(path)
    raise FileNotFoundError(
        f"None of {stem}.csv|.xlsx|.xls found in {RAW_DIR}/"
    )


def to_period(date_str: str) -> pd.Period:
    """YYYY-MM string → Period (monthly)."""
    return pd.Period(date_str, freq="M")


def safe_pct(new: float, old: float) -> float | None:
    """Percent change, rounded to 1 dp. None if old is missing/zero."""
    if old is None or old == 0 or pd.isna(old) or pd.isna(new):
        return None
    return round((new / old - 1) * 100, 1)


def series_to_payload(s: pd.Series, day: str = "01") -> list[dict]:
    """Convert a pandas Series indexed by Period → list of {d, v} dicts."""
    out = []
    for p, v in s.items():
        if pd.isna(v):
            continue
        out.append({"d": f"{p}-{day}", "v": round(float(v), 4)})
    return out


# ============================================================================
# PIPELINE STEPS
# ============================================================================
def process_prices(df: pd.DataFrame) -> dict:
    """WFP VAM: food basket indices, individual items, FX, wages."""
    print("→ Processing WFP prices...")

    # Parse dates (DD/MM/YYYY format from WFP exports)
    df["Price Date"] = pd.to_datetime(
        df["Price Date"], format="%d/%m/%Y", errors="coerce"
    )
    df = df[df["Price"].notna() & (df["Price"] > 0) & df["Price Date"].notna()]
    df["ym"] = df["Price Date"].dt.to_period("M")

    apr25 = to_period(COMPARISON_PERIOD)
    apr26 = to_period(ANCHOR_PERIOD)
    nov24 = to_period(PRE_END)

    # --- Basket indices ---
    basket_nb = [b for b in BASKET_FULL if b != "Bread (bakery)"]
    mc_full = (
        df[df["Commodity"].isin(BASKET_FULL)]
        .groupby(["ym", "Commodity"])["Price"]
        .median()
        .unstack()
    )
    mc_nb = (
        df[df["Commodity"].isin(basket_nb)]
        .groupby(["ym", "Commodity"])["Price"]
        .median()
        .unstack()
    )

    # Index Jan-2023 base = 100 (or first available month)
    base_full = mc_full.iloc[0]
    base_nb = mc_nb.iloc[0]
    idx_full_syp = (mc_full / base_full * 100).mean(axis=1)
    idx_nb_syp = (mc_nb / base_nb * 100).mean(axis=1)

    # USD-denominated baskets: divide by FX
    er = (
        df[df["Commodity"] == "Exchange rate (unofficial)"]
        .groupby("ym")["Price"]
        .median()
    )

    common_full = mc_full.index.intersection(er.index)
    mc_full_usd = mc_full.loc[common_full].div(er.loc[common_full], axis=0)
    idx_full_usd = (mc_full_usd / mc_full_usd.iloc[0] * 100).mean(axis=1)

    common_nb = mc_nb.index.intersection(er.index)
    mc_nb_usd = mc_nb.loc[common_nb].div(er.loc[common_nb], axis=0)
    idx_nb_usd = (mc_nb_usd / mc_nb_usd.iloc[0] * 100).mean(axis=1)

    # --- Combined basket time series for the chart ---
    basket_ts = []
    all_periods = sorted(set(idx_full_syp.index) | set(idx_full_usd.index))
    for p in all_periods:
        rec = {"d": f"{p}-01"}
        if p in idx_full_syp.index and pd.notna(idx_full_syp[p]):
            rec["syp_full"] = round(float(idx_full_syp[p]), 1)
        if p in idx_full_usd.index and pd.notna(idx_full_usd[p]):
            rec["usd_full"] = round(float(idx_full_usd[p]), 1)
        if p in idx_nb_syp.index and pd.notna(idx_nb_syp[p]):
            rec["syp_nb"] = round(float(idx_nb_syp[p]), 1)
        if p in idx_nb_usd.index and pd.notna(idx_nb_usd[p]):
            rec["usd_nb"] = round(float(idx_nb_usd[p]), 1)
        basket_ts.append(rec)

    # --- Bread series (separate bakery & shop) ---
    bakery_ts = series_to_payload(
        df[df["Commodity"] == "Bread (bakery)"].groupby("ym")["Price"].median()
    )
    shop_ts = series_to_payload(
        df[df["Commodity"] == "Bread (shop)"].groupby("ym")["Price"].median()
    )

    # --- Item-level YoY (for the bar chart) ---
    items_yoy = []
    for item in BASKET_FULL:
        if item not in mc_full.columns:
            continue
        if apr25 not in mc_full.index or apr26 not in mc_full.index:
            continue
        p1, p2 = mc_full.loc[apr25, item], mc_full.loc[apr26, item]
        pct = safe_pct(p2, p1)
        if pct is not None:
            items_yoy.append(
                {"name": item, "pre": float(p1), "post": float(p2), "pct": pct}
            )

    # Add shop bread for contrast
    shop = df[df["Commodity"] == "Bread (shop)"].groupby("ym")["Price"].median()
    if apr25 in shop.index and apr26 in shop.index:
        p1, p2 = shop[apr25], shop[apr26]
        items_yoy.append({
            "name": "Bread (shop, unsubsidized)",
            "pre": float(p1), "post": float(p2),
            "pct": safe_pct(p2, p1),
        })

    # --- FX series ---
    fx_ts = series_to_payload(er)

    # --- Wage in USD/month ---
    wage = (
        df[df["Commodity"] == "Wage (non-qualified labour)"]
        .groupby("ym")["Price"]
        .median()
    )
    common_w = wage.index.intersection(er.index)
    wage_usd_monthly = (
        wage.loc[common_w] * WORKING_DAYS_PER_MONTH / er.loc[common_w]
    )
    wage_ts_usd = series_to_payload(wage_usd_monthly)

    # --- KPIs (pulled from values above) ---
    fx_apr25 = float(er.get(apr25, 0)) or None
    fx_apr26 = float(er.get(apr26, 0)) or None
    wage_apr25 = float(wage.get(apr25, 0)) or None
    wage_apr26 = float(wage.get(apr26, 0)) or None

    kpis = {
        "basket_full_syp_yoy": safe_pct(idx_full_syp.get(apr26), idx_full_syp.get(apr25)),
        "basket_full_usd_yoy": safe_pct(idx_full_usd.get(apr26), idx_full_usd.get(apr25)),
        "basket_nb_syp_yoy":   safe_pct(idx_nb_syp.get(apr26),   idx_nb_syp.get(apr25)),
        "basket_nb_usd_yoy":   safe_pct(idx_nb_usd.get(apr26),   idx_nb_usd.get(apr25)),
        "fx_apr25": fx_apr25, "fx_apr26": fx_apr26,
        "fx_yoy":   safe_pct(fx_apr26, fx_apr25),
        "fx_trough": float(er[er.index >= to_period("2025-01")].min()),
        "bakery_yoy": safe_pct(
            mc_full.loc[apr26, "Bread (bakery)"] if apr26 in mc_full.index else None,
            mc_full.loc[apr25, "Bread (bakery)"] if apr25 in mc_full.index else None,
        ),
        "shop_yoy": safe_pct(shop.get(apr26), shop.get(apr25)),
        "wage_apr25_syp": wage_apr25,
        "wage_apr26_syp": wage_apr26,
        "wage_yoy_syp":   safe_pct(wage_apr26, wage_apr25),
        "wage_apr25_usd_month": (
            round(wage_apr25 * WORKING_DAYS_PER_MONTH / fx_apr25)
            if wage_apr25 and fx_apr25 else None
        ),
        "wage_apr26_usd_month": (
            round(wage_apr26 * WORKING_DAYS_PER_MONTH / fx_apr26)
            if wage_apr26 and fx_apr26 else None
        ),
    }

    return {
        "basket_ts":   basket_ts,
        "bakery_ts":   bakery_ts,
        "shop_ts":     shop_ts,
        "items_yoy":   items_yoy,
        "fx_ts":       fx_ts,
        "wage_ts_usd": wage_ts_usd,
        "kpis":        kpis,
    }


def process_ports() -> dict:
    """Combine 4 port-call files into monthly DWT series."""
    print("→ Processing port calls...")

    def to_monthly(stem: str) -> pd.DataFrame:
        d = load_table(stem)
        d["DateTime"] = pd.to_datetime(d["DateTime"])
        d["ym"] = d["DateTime"].dt.to_period("M")
        d["total"] = d[SHIP_COLS].sum(axis=1)
        return d.groupby("ym").agg(
            total=("total", "sum"),
            container=("Container", "sum"),
            drybulk=("Dry Bulk", "sum"),
            general=("General Cargo", "sum"),
            tanker=("Tanker", "sum"),
        )

    inc = to_monthly("port_incoming_tartus") + to_monthly("port_incoming_latakia")
    out = to_monthly("port_outgoing_tartus") + to_monthly("port_outgoing_latakia")

    apr25 = to_period(COMPARISON_PERIOD)
    apr26 = to_period(ANCHOR_PERIOD)

    port_ts = []
    for p in sorted(set(inc.index) | set(out.index)):
        port_ts.append({
            "d": f"{p}-01",
            "inc_total": float(inc.loc[p, "total"]) if p in inc.index else 0,
            "out_total": float(out.loc[p, "total"]) if p in out.index else 0,
            "inc_drybulk":   float(inc.loc[p, "drybulk"])   if p in inc.index else 0,
            "inc_container": float(inc.loc[p, "container"]) if p in inc.index else 0,
            "inc_general":   float(inc.loc[p, "general"])   if p in inc.index else 0,
            "inc_tanker":    float(inc.loc[p, "tanker"])    if p in inc.index else 0,
        })

    return {
        "port_ts": port_ts,
        "kpis": {
            "inc_dwt_apr25": float(inc.loc[apr25, "total"]) if apr25 in inc.index else None,
            "inc_dwt_apr26": float(inc.loc[apr26, "total"]) if apr26 in inc.index else None,
            "inc_dwt_yoy": safe_pct(
                inc.loc[apr26, "total"] if apr26 in inc.index else None,
                inc.loc[apr25, "total"] if apr25 in inc.index else None,
            ),
            "out_dwt_apr26": float(out.loc[apr26, "total"]) if apr26 in out.index else None,
            "out_dwt_yoy": safe_pct(
                out.loc[apr26, "total"] if apr26 in out.index else None,
                out.loc[apr25, "total"] if apr25 in out.index else None,
            ),
        },
    }


def process_remote_sensing() -> dict:
    """Nightlights (VIIRS) and NDVI from the merged remote-sensing file."""
    print("→ Processing remote sensing...")
    df = load_table("remote_sensing")
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values("ds")

    radiance_ts = [
        {"d": r["ds"].strftime("%Y-%m-%d"), "v": round(float(r["radiance"]), 4)}
        for _, r in df.iterrows() if pd.notna(r["radiance"])
    ]
    ndvi_ts = [
        {"d": r["ds"].strftime("%Y-%m-%d"), "v": round(float(r["ndvi"]), 4)}
        for _, r in df.iterrows() if pd.notna(r["ndvi"])
    ]

    # NDVI April 2026 is typically not available (1-month MODIS lag).
    # Use March-on-March as the agricultural-activity YoY anchor.
    def at(date_str: str, col: str) -> float | None:
        row = df[df["ds"] == date_str]
        if row.empty or pd.isna(row[col].iloc[0]):
            return None
        return float(row[col].iloc[0])

    return {
        "radiance_ts": radiance_ts,
        "ndvi_ts": ndvi_ts,
        "kpis": {
            "radiance_apr25": at("2025-04-01", "radiance"),
            "radiance_apr26": at("2026-04-01", "radiance"),
            "radiance_yoy":   safe_pct(at("2026-04-01", "radiance"),
                                       at("2025-04-01", "radiance")),
            "ndvi_mar25": at("2025-03-01", "ndvi"),
            "ndvi_mar26": at("2026-03-01", "ndvi"),
            "ndvi_yoy":   safe_pct(at("2026-03-01", "ndvi"),
                                   at("2025-03-01", "ndvi")),
        },
    }


# ============================================================================
# MAIN
# ============================================================================
def main() -> None:
    if not RAW_DIR.exists():
        sys.exit(f"✗ {RAW_DIR}/ not found. Create it and add raw data files.")

    print(f"Building from {RAW_DIR.resolve()}...")
    print()

    prices_data = process_prices(load_table("wfp_prices"))
    port_data = process_ports()
    rs_data = process_remote_sensing()

    # Merge KPIs from all sources
    kpis = {
        **prices_data.pop("kpis"),
        **port_data.pop("kpis"),
        **rs_data.pop("kpis"),
    }

    payload = {
        "meta": {
            "as_of": ANCHOR_PERIOD,
            "comparison_base": COMPARISON_PERIOD,
            "transition_date": TRANSITION_DATE,
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_files": sorted(p.name for p in RAW_DIR.iterdir()),
        },
        "kpis": kpis,
        **prices_data,
        **port_data,
        **rs_data,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(payload, f, separators=(",", ":"))

    size_kb = OUTPUT_FILE.stat().st_size / 1024
    print()
    print(f"✓ Wrote {OUTPUT_FILE} ({size_kb:.1f} KB)")
    print()
    print("Headline KPIs:")
    for k in [
        "basket_nb_syp_yoy", "basket_nb_usd_yoy", "fx_yoy",
        "bakery_yoy", "shop_yoy",
        "wage_yoy_syp", "wage_apr26_usd_month",
        "inc_dwt_yoy", "radiance_yoy", "ndvi_yoy",
    ]:
        v = kpis.get(k)
        if v is not None:
            unit = "%" if "yoy" in k or "pct" in k else ""
            prefix = "$" if "usd_month" in k else ""
            print(f"  {k:30s} {prefix}{v}{unit}")


if __name__ == "__main__":
    main()
