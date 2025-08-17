import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from PyPDF2 import PdfReader
from io import BytesIO

DATA_FILE = "data/ghg_records.csv"

# --- Top Indian companies with correct IR/sustainability pages ---
COMPANIES = [
    {"name": "Reliance Industries", "url": "https://www.ril.com/Sustainability/Reports.aspx"},
    {"name": "TCS", "url": "https://www.tcs.com/investors/annual-reports"},
    {"name": "Infosys", "url": "https://www.infosys.com/investors/reports-filings/annual-report.html"},
    {"name": "HDFC Bank", "url": "https://www.hdfcbank.com/aboutus/investor-relations/financial-information/annual-reports"},
    {"name": "ICICI Bank", "url": "https://www.icicibank.com/aboutus/annual-reports"},
]

# --- Extract text from PDF ---
def extract_from_pdf(url):
    try:
        r = requests.get(url, timeout=30)
        pdf = PdfReader(BytesIO(r.content))
        text = ""
        for page in pdf.pages[:10]:  # parse only first 10 pages for speed
            if page.extract_text():
                text += page.extract_text() + "\n"

        # Regex search
        scope1 = re.search(r"Scope[\s-]*1[^0-9]{0,10}([\d,\,\.]+.*?)\s?(tCO2e|MtCO2e|tons|tonnes)", text, re.IGNORECASE)
        scope2 = re.search(r"Scope[\s-]*2[^0-9]{0,10}([\d,\,\.]+.*?)\s?(tCO2e|MtCO2e|tons|tonnes)", text, re.IGNORECASE)
        scope3 = re.search(r"Scope[\s-]*3[^0-9]{0,10}([\d,\,\.]+.*?)\s?(tCO2e|MtCO2e|tons|tonnes)", text, re.IGNORECASE)
        re_energy = re.search(r"(renewable energy[^0-9]{0,10}([\d,\.]+)\s*%?)", text, re.IGNORECASE)

        return {
            "scope1": scope1.group(0) if scope1 else "",
            "scope2": scope2.group(0) if scope2 else "",
            "scope3": scope3.group(0) if scope3 else "",
            "renewable_energy": re_energy.group(0) if re_energy else "",
            "raw_info": text[:500]  # keep short preview
        }
    except Exception as e:
        return {"scope1": "", "scope2": "", "scope3": "", "renewable_energy": "", "raw_info": f"PDF error: {e}"}

# --- Crawl page and find PDF ---
def fetch_data(url):
    try:
        r = requests.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        pdf_link = ""
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.endswith(".pdf") and (
                "sustainability" in href.lower() or
                "annual" in href.lower() or
                "business responsibility" in href.lower()
            ):
                pdf_link = href
                if pdf_link.startswith("/"):
                    base = url.split("/")[0] + "//" + url.split("/")[2]
                    pdf_link = base + pdf_link
                break

        if pdf_link:
            return extract_from_pdf(pdf_link)
        else:
            return {"scope1": "", "scope2": "", "scope3": "", "renewable_energy": "", "raw_info": "No PDF found"}

    except Exception as e:
        return {"scope1": "", "scope2": "", "scope3": "", "renewable_energy": "", "raw_info": f"HTML error: {e}"}

# --- Main runner ---
def main():
    rows = []
    for c in COMPANIES:
        print(f"🔎 Scraping {c['name']} ...")
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
    df.to_csv(DATA_FILE, index=False, encoding="utf-8")
    print("✅ Data saved to", DATA_FILE)

if __name__ == "__main__":
    main()
