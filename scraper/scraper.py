import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from PyPDF2 import PdfReader
from io import BytesIO

DATA_FILE = "data/ghg_records.csv"

COMPANIES = [
    {"name": "Reliance Industries", "url": "https://www.ril.com/Sustainability/Reports.aspx"},
    {"name": "TCS", "url": "https://www.tcs.com/investors/annual-reports"},
    {"name": "Infosys", "url": "https://www.infosys.com/investors/reports-filings/annual-report.html"},
    {"name": "HDFC Bank", "url": "https://www.hdfcbank.com/aboutus/investor-relations/financial-information/annual-reports"},
    {"name": "ICICI Bank", "url": "https://www.icicibank.com/aboutus/annual-reports"},
]

def extract_from_pdf(url):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        pdf = PdfReader(BytesIO(r.content))
        text = ""
        for page in pdf.pages[:10]:  # only first 10 pages for speed
            if page.extract_text():
                text += page.extract_text() + "\n"

        # Regex search
        scope1 = re.search(r"Scope[\s-]*1[^0-9]{0,10}([\d,\.]+.*?(tCO2e|MtCO2e|tons|tonnes|CO2e))", text, re.IGNORECASE)
        scope2 = re.search(r"Scope[\s-]*2[^0-9]{0,10}([\d,\.]+.*?(tCO2e|MtCO2e|tons|tonnes|CO2e))", text, re.IGNORECASE)
        scope3 = re.search(r"Scope[\s-]*3[^0-9]{0,10}([\d,\.]+.*?(tCO2e|MtCO2e|tons|tonnes|CO2e))", text, re.IGNORECASE)
        re_energy = re.search(r"(renewable energy[^0-9]{0,10}([\d,\.]+)\s*%?)", text, re.IGNORECASE)

        return {
            "scope1": scope1.group(1) if scope1 else "",
            "scope2": scope2.group(1) if scope2 else "",
            "scope3": scope3.group(1) if scope3 else "",
            "renewable_energy": re_energy.group(1) if re_energy else "",
            "raw_info": text[:500]
        }
    except Exception as e:
        return {"scope1": "", "scope2": "", "scope3": "", "renewable_energy": "", "raw_info": f"PDF error: {e}"}

def fetch_data(url):
    try:
        r = requests.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        # find all PDF links
        pdf_link = ""
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().endswith(".pdf") and any(kw in href.lower() for kw in ["sustain", "annual", "esg"]):
                pdf_link = href
                if pdf_link.startswith("/"):
                    pdf_link = url.rsplit("/", 1)[0] + pdf_link
                break

        if pdf_link:
            return extract_from_pdf(pdf_link)
        else:
            return {"scope1": "", "scope2": "", "scope3": "", "renewable_energy": "", "raw_info": "No PDF found"}
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

    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(DATA_FILE, index=False)
    print("✅ Data updated:", DATA_FILE)

if __name__ == "__main__":
    main()
