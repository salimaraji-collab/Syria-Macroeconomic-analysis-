# Syria Macroeconomic Analysis — April 2026

Internal briefing dashboard for the UN Resident Coordinator, Syria. Single-page interactive analysis of Syria's post-transition macroeconomic situation, anchored on April 2026 data with year-on-year comparisons against April 2025.

**Prepared by:** Senior Economist Office, UN RCO Damascus
**Audience:** Resident Coordinator, Syria
**Status:** Internal background brief

## What this dashboard covers

- **Summary** — single-paragraph synthesis of the post-transition trajectory
- **Strategic readings** — seven anchor numbers with one-sentence interpretations
- **Evidence** — six tabbed sections, each with chart and two-paragraph analysis:
  - 🍞 Food (basket evolution, item-level changes, bakery vs shop bread)
  - 💱 Exchange rate (USD/SYP parallel)
  - 💵 Wages (unskilled monthly USD wage, real purchasing power)
  - 🌃 Nightlights (VIIRS radiance, economic-activity proxy)
  - 🌾 Agriculture (MODIS NDVI, agricultural-activity proxy)
  - ⚓ Ports (Tartus + Latakia DWT)

## How to view locally

The dashboard is a single self-contained HTML file. To preview:

```bash
# Option 1: open directly in a browser
open index.html  # macOS
xdg-open index.html  # Linux
start index.html  # Windows

# Option 2: serve locally (recommended — avoids file:// quirks)
python3 -m http.server 8000
# then open http://localhost:8000
```

## How to deploy on GitHub Pages

1. Push this repo to GitHub (any name, public or private with Pages enabled).
2. Go to **Settings → Pages**.
3. Under **Source**, select **Deploy from a branch**.
4. Choose the `main` branch and `/ (root)` folder, then click **Save**.
5. Wait ~1–2 minutes. Your dashboard will be live at:
   `https://<your-username>.github.io/<repo-name>/`

That's it — no build step required.

## Alternative: deploy on Vercel

1. Push this repo to GitHub.
2. Go to [vercel.com/new](https://vercel.com/new), import the repo.
3. Accept the default settings (no build command, root directory).
4. Click **Deploy**.

The dashboard will be live at `https://<project-name>.vercel.app` within a minute, with automatic redeploys on every push.

## Technical details

- **Single file:** `index.html`. All data, styles, and scripts are inline.
- **No build step:** open it, push it to GitHub Pages, or drop it on any static host.
- **Dependencies (loaded from CDN):**
  - Chart.js 4.4.0
  - chartjs-adapter-date-fns 3.0.0
  - chartjs-plugin-annotation 3.0.1
- **Data anchor:** April 2026
- **Comparison frame:** April 2025 → April 2026 (YoY)
- **Pre-transition reference:** January–November 2024
- **Transition date:** 8 December 2024 (fall of the Assad regime)

## Data sources

- **WFP Syria VAM** — food prices, unskilled wage, parallel exchange rate (73 markets)
- **Tartus + Latakia port-call data** — vessel deadweight tonnage, daily, 2019 → April 2026
- **NASA VIIRS Black Marble** — nightlights radiance (mean monthly over Syria)
- **MODIS NDVI** — vegetation index (mean monthly over Syria)

## Methodological notes

- **Port-call DWT measures vessel carrying capacity, not cargo volumes.** Customs data would be needed to convert to actual goods imported. The portal flags this caveat in the Ports section.
- **Wages are reported in USD/month** (daily SYP wage × 22 working days ÷ unofficial USD/SYP rate). This strips out FX-driven nominal change to leave only the real purchasing-power signal.
- **Bread is presented as two separate items** (bakery vs shop) because the December 2024 subsidy reset created a one-time level shift in bakery bread that distorts any aggregated bread-inclusive food index.
- **NDVI YoY comparison uses March, not April,** because April 2026 NDVI is not yet published (MODIS NDVI has approximately a one-month publication lag).

## Updating the dashboard

The dashboard is currently a static snapshot. To produce an updated version with newer data:

1. Refresh the underlying datasets (WFP VAM export, port-call data, VIIRS, MODIS).
2. Re-run the data-preparation pipeline to regenerate the inline JSON payload.
3. Replace the `const DATA = {...}` line in `index.html` with the new payload.
4. Update the `as_of` and `comparison` strings in the document header.
5. Commit and push — GitHub Pages will redeploy automatically.

## Repository structure

```
.
├── index.html        # The dashboard (self-contained)
├── README.md         # This file
└── .gitignore        # Standard ignores
```

## License & confidentiality

Internal UN RCO Damascus document. Not for external distribution without RC clearance.
