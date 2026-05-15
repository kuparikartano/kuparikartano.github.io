# Taloyhtiö

A small Jekyll-based site for a housing company, with a trash-pickup page
whose dates are scraped daily from
[HSY:n raporttipalvelu](https://raportit.hsy.fi/report/) by GitHub Actions.

## What's in here

```
.
├── _config.yml                    Jekyll config + HSY identifiers
├── _data/trash.yml                Auto-generated; do not hand-edit
├── _layouts/, _includes/, assets/ Theme
├── index.md                       Front page
├── roskat.md                      Trash pickup page
├── yhteystiedot.md, info.md       Placeholder pages
├── scripts/
│   ├── scrape_trash.py            Playwright scraper
│   └── requirements.txt
└── .github/workflows/
    ├── scrape-trash.yml           Daily scrape → commit _data/trash.yml
    └── pages.yml                  Build & deploy Jekyll to GitHub Pages
```

The site is intentionally tiny and uses no third-party Jekyll theme — all
markup lives in `_layouts/default.html` and `assets/style.css`.

## How it works

1. **`scrape-trash.yml`** runs daily at 04:17 UTC.
   It checks out the repo, installs `requests` + PyYAML, runs
   `scripts/scrape_trash.py`, and commits the updated `_data/trash.yml`
   back to `main` if anything changed. The whole run takes seconds.
2. The push triggers **`pages.yml`**, which builds the Jekyll site and
   deploys it to GitHub Pages.
3. The trash page (`roskat.md`) reads `site.data.trash` and renders the
   list of containers plus a "next pickup" highlight.

The scraper calls HSY's undocumented but unauthenticated "ajax-open"
JSON endpoint that the SPA itself uses:

    GET https://raportit.hsy.fi/report/ajax-open/stats/description/waste/{service}/{postal}/{customer}/fi

No API key is required. If HSY changes the endpoint the scraper will
start failing; re-run with `--debug-dir` to inspect the raw payload, or
re-discover the URL in browser DevTools and update `API_BASE` in
`scripts/scrape_trash.py`.

## Configuring your property

The HSY identifiers are stored at the top of `_config.yml`:

```yaml
hsy:
  service_number: "BB11-012731-0"  # jätepalvelutunnus
  postal_code:    "00410"          # postinumero
  customer_id:    "72603608934"    # asiakas / laskunumero
```

These come from the URL HSY gives you, of the form:
`https://raportit.hsy.fi/report/#/fi/serviceDescription/<service>/<postal>/<customer>////`

You can override them per-run via the workflow's `workflow_dispatch`
inputs in the GitHub Actions UI without editing the config.

## Setting up the repo on GitHub

1. Create a new repository on GitHub and push this directory to it as `main`.
2. In the repo, go to **Settings → Pages** and set **Source = GitHub Actions**.
3. Make sure **Settings → Actions → General → Workflow permissions** is set to
   **Read and write permissions** (or grant `contents: write` explicitly — the
   workflow declares the permission, but the org/repo policy must allow it).
4. Trigger the first run manually:
   **Actions → Scrape trash pickup dates → Run workflow**. This will commit
   the first `_data/trash.yml` and kick off the Pages deploy.
5. The site will be live at `https://<your-username>.github.io/<repo>/`.

If you deploy as a *project page* (e.g. `…/taloyhtio/`), Jekyll will pick
up the right base path automatically — `pages.yml` passes
`--baseurl "${{ steps.pages.outputs.base_path }}"` for you.

## Running things locally

### Jekyll preview

```bash
bundle install
bundle exec jekyll serve
# open http://127.0.0.1:4000/
```

### Run the scraper locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt

python scripts/scrape_trash.py
# or with debug dump:
python scripts/scrape_trash.py --debug-dir .scrape-debug
```

The script writes `_data/trash.yml`. The `--debug-dir` flag also dumps
the raw JSON payload — useful if HSY changes the endpoint and the
scraper stops finding container records.

## Why this endpoint instead of HSY's documented API?

HSY's [documented eRaportti REST API](https://lukemat.hsy.fi/raportti-rajapinta.html)
gives clean JSON, but it requires:

- an `X-API-KEY` obtained by email,
- a "koontiraportti" (composite report) created in eRaportti, whose
  `listId` you'd pass to `…/v1/details/waste/{listId}/{language}`.

The `ajax-open` endpoint the SPA itself uses needs none of that — it's
the same JSON, but keyed on your `service` / `postal` / `customer`
triple straight from the public report URL.

## Customising the site

- **Pages**: add a new `.md` file in the repo root with a front-matter
  block. Add a link to it in `_includes/nav.html`.
- **Theme**: edit `assets/style.css` and `_layouts/default.html`.
- **Schedule**: change the `cron:` line in `.github/workflows/scrape-trash.yml`.

## Licence

Choose your own — the code is generic enough to drop into anything.
