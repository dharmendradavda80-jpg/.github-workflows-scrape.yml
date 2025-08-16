import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

DATA_FILE = "data/ghg_records.csv"

# Example: Top 5 NSE companies with dummy ESG URLs (replace with real ones later)
COMPANIES = [
    {"name": "Reliance Industries", "url": "https://www.ril.com/Sustainability/Reports.aspx"},
    {"name": "TCS", "url": "https://www.tcs.com/sustainability"},
    {"name": "Infosys", "url": "https://www.infosys.com/sustainability"},
    {"name": "HDFC Bank", "url": "https://www.hdfcbank.com/sustainability"},
    {"name": "ICICI Bank", "url": "https://www.icicibank.com/aboutus/sustainability"},
]

def fetch_data(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        # 🔹 Simplified: just return the page title now
        return soup.title.string if soup.title else "No data"
    except:
        return "Error fetching"

def main():
    rows = []
    for c in COMPANIES:
        info = fetch_data(c["url"])
        rows.append({
            "company": c["name"],
            "url": c["url"],
            "raw_info": info
        })
    df = pd.DataFrame(rows)

    os.makedirs("data", exist_ok=True)
    df.to_csv(DATA_FILE, index=False)
    print("✅ Data updated:", DATA_FILE)

if __name__ == "__main__":
    main()
