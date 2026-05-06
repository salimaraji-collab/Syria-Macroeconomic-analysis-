# Syria Macroeconomic Analysis — UN RCO Damascus

Internal interactive dashboard for the Resident Coordinator. Reads raw WFP, port, and remote-sensing data files, processes them into analytical aggregates, and renders an evidence-tabbed brief on Syria's post-transition macroeconomy.

**Audience:** Resident Coordinator, Syria
**Anchor:** April 2026
**Comparison:** April 2025 → April 2026 (year-on-year)
**Status:** Internal background brief

---

## How this repo works

```
syria-macro-brief/
├── data/
│   ├── raw/                ← YOU EDIT THIS — drop your data files here
│   │   ├── wfp_prices.csv
│   │   ├── port_incoming_tartus.csv
│   │   ├── port_incoming_latakia.csv
│   │   ├── port_outgoing_tartus.csv
│   │   ├── port_outgoing_latakia.csv
│   │   └── remote_sensing.csv
│   └── processed.json      ← AUTO-GENERATED — what the dashboard reads
├── build.py                ← Python pipeline that produces processed.json
├── index.html              ← The dashboard (fetches processed.json on load)
├── .github/workflows/
│   └── build.yml           ← Runs build.py on every push, deploys to Pages
├── README.md
└── .gitignore
```

The flow:
1. You drop updated data files in `data/raw/`
2. Push to GitHub
3. GitHub Actions runs `build.py` automatically
4. The dashboard regenerates and redeploys to GitHub Pages
5. Live URL refreshes within ~2 minutes

You don't need Python on your laptop. The whole pipeline runs in GitHub's cloud.

---

## Updating the dashboard with new data

Two paths depending on whether you have Python locally:

### Option A: just push the raw files (recommended)

1. Replace any file in `data/raw/` with the new vintage. Keep the **same filename** (the build script looks for specific stems).
2. `git add data/raw/wfp_prices.csv && git commit -m "Update WFP prices to May 2026" && git push`
3. Wait 60–90 seconds. Check the **Actions** tab on GitHub to watch it build. The dashboard URL refreshes when the green check appears.

### Option B: build locally then push

If you want to preview before pushing:

```bash
pip install pandas openpyxl
python build.py
# now open index.html via a local server and check it looks right
python3 -m http.server 8000
# visit http://localhost:8000
```

Then commit and push as in Option A.

---

## Data file expectations

`build.py` accepts `.csv`, `.xlsx`, or `.xls` for any file. Filenames must match these stems exactly:

| File stem                      | Source                       | Required columns                                             |
|--------------------------------|------------------------------|---------------------------------------------------------------|
| `wfp_prices`                   | WFP VAM Syria export         | `Price Date` (DD/MM/YYYY), `Commodity`, `Market Name`, `Price`, `Unit` |
| `port_incoming_tartus`         | Port-call data, Tartus       | `DateTime`, `Container`, `Dry Bulk`, `General Cargo`, `Roll-on/roll-off`, `Tanker` |
| `port_incoming_latakia`        | Port-call data, Latakia      | same as above                                                |
| `port_outgoing_tartus`         | Port-call data, Tartus       | same as above                                                |
| `port_outgoing_latakia`        | Port-call data, Latakia      | same as above                                                |
| `remote_sensing`               | Pre-merged VIIRS + MODIS     | `ds` (date), `radiance`, `ndvi`                              |

If a column name changes upstream (e.g. WFP renames "Commodity" to something else), edit the constants at the top of `build.py`.

---

## Tweaking the analysis

Edit the configuration block at the top of `build.py`:

```python
ANCHOR_PERIOD     = "2026-04"   # the "as of" month
COMPARISON_PERIOD = "2025-04"   # YoY base

WORKING_DAYS_PER_MONTH = 22     # used to convert daily wage → monthly USD

BASKET_FULL = [...]             # the 13 items in the WFP basket
```

To change copy in the dashboard (strategic reading text, panel titles, analysis paragraphs), edit `index.html` directly. The text is plain HTML — no build step touches it.

---

## Deploy on GitHub Pages

1. Push this repo to GitHub.
2. **Settings → Pages → Source: GitHub Actions** (NOT "Deploy from a branch" — the workflow handles deployment).
3. The first push triggers the workflow. Subsequent deployments happen automatically.
4. Live URL: `https://<your-username>.github.io/<repo-name>/`

The workflow (`.github/workflows/build.yml`) handles everything: install Python, run `build.py`, deploy. You don't run anything locally.

---

## Deploy on Vercel (alternative)

1. Push to GitHub.
2. [vercel.com/new](https://vercel.com/new) → import the repo.
3. Build command: `python build.py`
4. Output directory: `.` (the repo root)
5. Install command: `pip install pandas openpyxl`

Vercel works for **private** GitHub repos on its free tier; GitHub Pages requires a paid GitHub plan for that.

---

## Methodological notes

These are the analytical choices baked into `build.py` and the dashboard. They're documented here in case a successor needs to defend them.

- **Year-on-year (April-to-April) is the comparison frame.** Comparing to November 2024 (the immediate pre-transition baseline) systematically overstates stabilization because it anchors against the FX appreciation peak of mid-2025. YoY against April 2025 is cleaner.
- **Wages reported in USD/month.** Daily SYP wage × 22 working days ÷ unofficial USD/SYP rate. This strips out FX-driven nominal change, leaving the real purchasing-power signal. The +42% nominal SYP figure overstates the real gain by ~16 pp.
- **Bakery and shop bread are tracked separately.** The December 2024 subsidy reset created a one-time level shift in bakery bread (+640% Nov→Apr) that distorts any aggregated bread-inclusive food index. The two indices (with/without bread) are both shown so the bread effect is visible at a glance.
- **Port-call DWT measures vessel carrying capacity, not goods unloaded.** Customs data would be needed for cargo volumes. The portal flags this caveat in the Ports section.
- **NDVI YoY uses March, not April.** April 2026 NDVI is typically not yet published when the dashboard is updated (MODIS NDVI has approximately a one-month lag). March-on-March is the cleanest agricultural-activity comparison available.

---

## Sources

- **WFP Syria VAM** — food prices, unskilled wage, parallel exchange rate (73 markets)
- **Port-call data, Tartus + Latakia** — daily vessel DWT, 2019 → present
- **NASA VIIRS Black Marble** — nightlights radiance (mean monthly over Syria)
- **MODIS NDVI** — vegetation index (mean monthly over Syria)

---

## Confidentiality

Internal UN RCO Damascus document. Make the GitHub repo **private** before pushing, unless the RC has cleared external publication.
