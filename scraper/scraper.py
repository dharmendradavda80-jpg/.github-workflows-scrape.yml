name: Run ESG Scraper

on:
  workflow_dispatch:   # run manually
  schedule:
    - cron: "0 0 * * 0"   # run every Sunday at midnight UTC

jobs:
  build:
    runs-on: ubuntu-latest

    permissions:
      contents: write   # allow pushing changes

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4 pandas PyPDF2

      - name: Run scraper
        run: python scraper.py

      - name: Save CSV snapshot with date
        run: |
          mkdir -p data/history
          DATE=$(date +'%Y-%m-%d')
          cp data/ghg_records.csv data/history/ghg_records_$DATE.csv

      - name: Commit updated CSVs
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add data/ghg_records.csv
          git add data/history/
          git commit -m "Auto-update ESG data ($DATE) [skip ci]" || echo "No changes to commit"
          git push
df.to_csv("data/ghg_records.csv", index=False)
