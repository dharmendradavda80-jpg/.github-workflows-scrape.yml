import os
import re
import pandas as pd
import requests
from PyPDF2 import PdfReader
from io import BytesIO

DATA_FILE = "data/ghg_records.csv"

# Hardcoded PDFs per company
COMPANIES = [
    {"name": "Reliance Industries", "pdf_url": "https://www.ril.com/reports/RIL-Integrated-Annual-Report-2024-25.pdf"},
    {"name": "TCS", "pdf_url": "https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2023-24/ar/annual-report-2023-2024.pdf"},
    {"name": "Infosys", "pdf_url": "https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-25.pdf"},
    {"name": "HDFC Bank", "pdf_url": "https://www.hdfcbank.com/content/api/contentstream/723fb80a-2dde-42a3-9793-7ae1be57c87f/Footer/About%20Us/Investor%20Relation/annual%20reports/pdf/Integrated%20Annual%20Report%202022-23.pdf"},
    {"name": "ICICI Bank", "pdf_url": "https://www.icicibank.com/content/dam/icicibank/managed-assets/docs/investor/annual-reports/2024/annual-report-of-icici-bank-2023-24.pdf"},
]

def extract_from_pdf(url: str):
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        pdf = PdfReader(BytesIO(r.content))
        text = "".join(page.extract_text() or "" for page in pdf.pages[:10])

        scope1 = re.search(r"Scope[\s-]*1[^0-9]{0,10}([\d,\.]+.*?)", text, re.IGNORECASE)
        scope2 = re.search(r"Scope[\s-]*2[^0-9]{0,10}([\d,\.]+.*?)", text, re.IGNORECASE)
        scope3 = re.search(r"Scope[\s-]*3[^0-9]{0,10}([\d,\.]+.*?)", text, re.IGNORECASE)
        re_energy = re.search(r"(renewable energy[^0-9]{0,10}([\d,\.]+)\s*%?)", text, re.IGNORECASE)

        return {
            "scope1": scope1.group(1) if scope1 else "",
            "scope2": scope2.group(1) if scope2 else "",
            "scope3": scope3.group(1) if scope3 else "",
            "renewable_energy": re_energy.group(1) if re_energy else "",
            "raw_info": text[:500],
        }
    except Exception as e:
        return {"scope1": "", "scope2": "", "scope3": "", "renewable_energy": "", "raw_info": f"Error: {e}"}

def main():
    os.makedirs("data", exist_ok=True)
    rows = []
    for c in COMPANIES:
        info = extract_from_pdf(c["pdf_url"])
        rows.append({
            "company": c["name"],
            "url": c["pdf_url"],
            **info
        })
    pd.DataFrame(rows).to_csv(DATA_FILE, index=False, encoding="utf-8")
    print("✅ ghg_records.csv updated")

if __name__ == "__main__":
    main()
