import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

DATA_FILE = "data/ghg_records.csv"

COMPANIES = [
    {"name": "Reliance Industries", "url": "https://www.ril.com/Sustainability/Reports.aspx"},
    {"name": "Infosys", "url": "https://www.infosys.com/sustainability"},
]

def fetch_data(url):
    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        # Simple test: just check if words "Scope 1/2/3" exist
        return {
            "scope1": "FOUND" if "scope 1" in text.lower() else "",
            "scope2": "FOUND" if "scope 2" in text.lower() else "",
            "scope3": "FOUND" if "scope 3" in text.lower() else "",
            "raw_info": text[:300]
        }
    except Exception as e:
        return {"scope1": "", "scope2": "", "scope3": "", "raw_info": f"Error: {e}"}

def main():
    os.makedirs("data", exist_ok=True)
    rows = []
    for c in COMPANIES:
        info = fetch_data(c["url"])
        rows.append({"company": c["name"], "url": c["url"], **info})
    df = pd.DataFrame(rows)
    df.to_csv(DATA_FILE, index=False)
    print("✅ Data written to", DATA_FILE)

if __name__ == "__main__":
    main()
