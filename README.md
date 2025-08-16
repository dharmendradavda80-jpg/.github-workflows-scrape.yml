# NSE GHG Scraper

This repo automatically scrapes ESG / GHG disclosure data from top NSE-listed companies.

- Data stored in: `data/ghg_records.csv`
- Workflow: `.github/workflows/scrape.yml`
- Runs: Daily (via GitHub Actions)

## How it works
- GitHub Actions triggers `run_all.py`
- Python scrapes ESG/annual report pages
- Results are saved in CSV
- Data is updated every day
