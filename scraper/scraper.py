import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from PyPDF2 import PdfReader
from io import BytesIO

# Fake browser headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

DATA_FILE = "data/ghg_records.csv"

COMPANIES = [
    {"name": "Reliance Industries", "url": "https://www.ril.com/Sustainability/Reports.aspx"},
    {"name": "TCS", "url": "https://www.tcs.com/investors/annual-reports"},
    {"name": "Infosys", "url": "https://www.infosys.com/investors/reports-filings/annual-report.html"},
    {"name": "HDFC Bank", "url": "https://www.hdfcbank.com/aboutus/investor-relations/financial-information/annual-reports"},
    {"name": "ICICI Bank", "url": "https://www.icicibank.com/aboutus/annual-reports"},
]

def extract_from_pdf(url: str):
    """Download a PDF and try to extract Scope 1, 2, 3 data"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        pdf = PdfReader(BytesIO(r.content))
        text = ""
        for page in pdf.pages[:10]:  # only scan first 10 pages for speed
            text += page.extract_text() + "\n"

        # Regex search for Scope 1/2/3
        scope1 = re.search(r"Scope[\s-]*1[^0-9]{0,10}([\d,.,]+.*?)\s?(tCO2e|MtCO2e|tons|tonnes|CO2e)?", text, re.IGNORECASE)
        scope2 = re.search(r"Scope[\s-]*2[^0-9]{0,10}([\d,.,]+.*?)\s?(tCO2e|MtCO2e|tons|tonnes|CO2e)?", text, re.IGNORECASE)
        scope3 = re.search(r"Scope[\s-]*3[^0-9]{0,10}([\d,.,]+.*?)\s?(tCO2e|MtCO2e|tons|tonnes|CO2e)?", text, re.IGNORECASE)

        return {
            "scope1": scope1.group(0) if scope1 else "",
            "scope2": scope2.group(0) if scope2 else "",
            "scope3": scope3.group(0) if scope3 else ""
        }
    except Exception as e:
        return {"scope1": "", "scope2": "", "scope3": "", "error": f"PDF error: {e}"}


def fetch_data(url: str):
    """Scrape the company sustainability/annual report page"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(" ", strip=True)

        # Try to find a PDF link
        pdf_link = ""
        for a in soup.find_all("a", href=True):
            if "report" in a.text.lower() and a['href'].endswith(".pdf"):
                pdf_link = a["href"]
                if pdf_link.startswith("/"):
                    pdf_link = url.rsplit("/", 1)[0] + pdf_link
                break

        # Extract PDF data
        pdf_data = extract_from_pdf(pdf_link) if pdf_link else {"scope1": "", "scope2": "", "scope3": ""}

        return {
            "scope1": pdf_data.get("scope1", ""),
            "scope2": pdf_data.get("scope2", ""),
            "scope3": pdf_data.get("scope3", ""),
            "renewable_energy": "",  # we can add later
            "raw_info": text[:500] if text else "No text found",
        }

    except Exception as e:
        return {"scope1": "", "scope2": "", "scope3": "", "renewable_energy": "", "raw_info": f"Error: {e}"}


def main():
    rows = []
    for c in COMPANIES:
        print(f"🔎 Fetching {c['name']} ...")
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
