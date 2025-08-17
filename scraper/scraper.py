import os
import re
import pandas as pd
import requests
from PyPDF2 import PdfReader
from io import BytesIO
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

DATA_FILE = "data/ghg_records.csv"

COMPANIES = [
    {"name": "Reliance Industries", "url": "https://www.ril.com/Sustainability/Reports.aspx"},
    {"name": "TCS", "url": "https://www.tcs.com/investors/annual-reports"},
    {"name": "Infosys", "url": "https://www.infosys.com/investors/reports-filings/annual-report.html"},
    {"name": "HDFC Bank", "url": "https://www.hdfcbank.com/aboutus/investor-relations/financial-information/annual-reports"},
    {"name": "ICICI Bank", "url": "https://www.icicibank.com/aboutus/annual-reports"},
]

def extract_from_pdf(url):
    """Download and extract Scope data from a PDF."""
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        pdf = PdfReader(BytesIO(r.content))
        text = ""
        for page in pdf.pages[:10]:  # only scan first 10 pages for performance
            if page.extract_text():
                text += page.extract_text() + "\n"

        scope1 = re.search(r"Scope[\s-]*1[^0-9]{0,10}([\d,\.]+.*?)", text, re.IGNORECASE)
        scope2 = re.search(r"Scope[\s-]*2[^0-9]{0,10}([\d,\.]+.*?)", text, re.IGNORECASE)
        scope3 = re.search(r"Scope[\s-]*3[^0-9]{0,10}([\d,\.]+.*?)", text, re.IGNORECASE)

        return {
            "scope1": scope1.group(1) if scope1 else "",
            "scope2": scope2.group(1) if scope2 else "",
            "scope3": scope3.group(1) if scope3 else ""
        }
    except Exception as e:
        return {"scope1": "", "scope2": "", "scope3": ""}

def scrape_with_playwright():
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for c in COMPANIES:
            try:
                page.goto(c["url"], timeout=60000)
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                text = soup.get_text(" ", strip=True)

                # Find a PDF link on the page
                pdf_link = ""
                for a in soup.find_all("a", href=True):
                    if a['href'].lower().endswith(".pdf"):
                        pdf_link = a['href']
                        if pdf_link.startswith("/"):
                            base = c["url"].rsplit("/", 1)[0]
                            pdf_link = base + pdf_link
                        break

                if pdf_link:
                    pdf_data = extract_from_pdf(pdf_link)
                else:
                    pdf_data = {"scope1": "", "scope2": "", "scope3": ""}

                rows.append({
                    "company": c["name"],
                    "url": c["url"],
                    "scope1": pdf_data["scope1"],
                    "scope2": pdf_data["scope2"],
                    "scope3": pdf_data["scope3"],
                    "renewable_energy": "",
                    "raw_info": text[:500] if text else "No text"
                })

            except Exception as e:
                rows.append({
                    "company": c["name"],
                    "url": c["url"],
                    "scope1": "",
                    "scope2": "",
                    "scope3": "",
                    "renewable_energy": "",
                    "raw_info": f"Error: {e}"
                })

        browser.close()
    return rows

def main():
    os.makedirs("data", exist_ok=True)
    rows = scrape_with_playwright()
    df = pd.DataFrame(rows)
    df.to_csv(DATA_FILE, index=False)
    print("✅ Data updated:", DATA_FILE)

if __name__ == "__main__":
    main()
