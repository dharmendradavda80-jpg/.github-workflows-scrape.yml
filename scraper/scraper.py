import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

DATA_FILE = "data/ghg_records.csv"

COMPANIES = [
    {"name": "Reliance Industries", "url": "https://www.ril.com/Sustainability/Reports.aspx"},
    {"name": "TCS", "url": "https://www.tcs.com/sustainability"},
    {"name": "Infosys", "url": "https://www.infosys.com/sustainability"},
    {"name": "HDFC Bank", "url": "https://www.hdfcbank.com/sustainability"},
    {"name": "ICICI Bank", "url": "https://www.icicibank.com/aboutus/sustainability"},
]

def fetch_data(url):
    try:
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(" ", strip=True)
        text = " ".join(text.split())  # clean extra spaces

        # Regex patterns
        scope1 = re.search(r"(Scope[\s-]*1[^0-9]{0,10}([\d,\.]+)\s*(tCO2e|MtCO2e|tons|tonnes)?)", text, re.IGNORECASE)
        scope2 = re.search(r"(Scope[\s-]*2[^0-9]{0,10}([\d,\.]+)\s*(tCO2e|MtCO2e|tons|tonnes)?)", text, re.IGNORECASE)
        scope3 = re.search(r"(Scope[\s-]*3[^0-9]{0,10}([\d,\.]+)\s*(tCO2e|MtCO2e|tons|tonnes)?)", text, re.IGNORECASE)
        re_energy = re.search(r"(renewable energy[^0-9]{0,10}([\d,\.]+)\s*%?)", text, re.IGNORECASE)

        return {
            "scope1": scope1.group(1) if scope1 else "",
            "scope2": scope2.group(1) if scope2 else "",
            "scope3": scope3.group(1) if scope3 else "",
            "renewable_energy": re_energy.group(1) if re_energy else "",
            "raw_info": text[:500]  # store only first 500 chars for context
        }

    except Exception as e:
        return {"scope1": "", "scope2": "", "scope3": "", "renewable_energy": "", "raw_info": f"Error: {e}"}

def main():
    rows = []
    for c in COMPANIES:
        info = fetch_data(c["url"])
        rows.append({
            "company": c["name"],
            "url": c["url"],
            "scope1": info["scope1"],
            "scope2": info["scope2"],
            "scope3": info["scope3"],
            "renewable_energy": info["renewable_energy"],
            "raw_info": info["raw_info"]
        })
    df = pd.DataFrame(rows)

    os.makedirs("data", exist_ok=True)
    df.to_csv(DATA_FILE, index=False)
    print("✅ Data updated:", DATA_FILE)

if __name__ == "__main__":
    main()
