# Deployment — one-time setup

The site is published by a GitHub Actions workflow defined in
`.github/workflows/build.yml`. On every push to `main` it:

1. installs the Python dependencies from `requirements.txt`,
2. runs `build.py` (regenerates `data/processed.json` from the raw files in `data/raw/`),
3. uploads the whole repo as a Pages artifact,
4. deploys it to GitHub Pages.

For the workflow's output to actually become the live site, **the
"Source" setting in GitHub Pages has to be set to "GitHub Actions"
once**. This is the step that was missing — it's why your phone got a
404 from `araji-collab.github.io`.

## One-time setup (on a computer, not phone)

1. Open the repo on github.com.
2. Click **Settings** (top-right of the repo tabs).
3. In the left sidebar, scroll to **Pages**.
4. Under **"Build and deployment"** → **Source**, choose **"GitHub Actions"**.
   *(Do NOT pick "Deploy from a branch" — that mode ignores the workflow.)*
5. Save.

## Trigger the first deployment

Either:

- **Push any change to `main`** — the workflow auto-runs, or
- Open the **Actions** tab → "Build and deploy dashboard" workflow → click
  **"Run workflow"** → branch `main` → green button.

Watch the run. When both `build` and `deploy` show a green check, click
the `deploy` job — the URL appears under "Deploy to GitHub Pages" as the
`page_url` output.

## The live URL

For a repo named `Syria-Macroeconomic-analysis` owned by `araji-collab`,
the Pages URL is:

```
https://araji-collab.github.io/Syria-Macroeconomic-analysis/
```

The repo name on the end is required. Plain `araji-collab.github.io`
will 404 unless there's a special repo named exactly
`araji-collab.github.io`.

## Alternative — Vercel

`vercel.json` is also in the repo, so the project deploys cleanly on
Vercel with no extra setup. On Vercel:

1. vercel.com/new → "Import Git Repository" → select this repo.
2. Click **Deploy**. The `buildCommand` in `vercel.json` already runs
   `pip install -r requirements.txt && python build.py`.
3. After ~60s Vercel gives you a `something.vercel.app` URL.

This is often the faster path. The two deployment targets (Pages and
Vercel) don't conflict — both can run side-by-side.
