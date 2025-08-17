import pandas as pd
import requests
from PyPDF2 import PdfReader
from io import BytesIO

# Hardcoded correct URLs for each company
COMPANIES = [
    {
        "company": "Reliance Industries",
        "url": "https://www.ril.com/reports/RIL-Integrated-Annual-Report-2024-25.pdf",
    },
    {
        "company": "TCS",
        "url": "https://www.tcs.com/content/dam/tcs/investor-relations/financial-statements/2023-24/ar/annual-report-2023-2024.pdf",
    },
    {
        "company": "Infosys",
        "url": "https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-25.pdf",
    },
    {
        "company": "HDFC Bank",
        "url": "https://www.hdfcbank.com/content/api/contentstream/723fb80a-2dde-42a3-9793-7ae1be57c87f/Footer/About%20Us/Investor%20Relation/annual%20reports/pdf/Integrated%20Annual%20Report%202022-23.pdf",
    },
    {
        "company": "ICICI Bank",
        "url": "https://www.icicibank.com/content/dam/icicibank/managed-assets/docs/investor/annual-reports/2024/annual-report-of-icici-bank-2023-24.pdf",
    },
]

OUTPUT_FILE = "scraped_reports.csv"


def extract_pdf_text(url: str) -> str:
    """Download a PDF and extract its text."""
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        pdf = PdfReader(BytesIO(response.content))

        text = []
        for page in pdf.pages[:5]:  # limit to first 5 pages for speed
            text.append(page.extract_text() or "")

        return "\n".join(text).strip()

    except Exception as e:
        return f"Error extracting PDF: {e}"


def main():
    rows = []

    for entry in COMPANIES:
        company = entry["company"]
        url = entry["url"]

        print(f"Processing {company}...")
        text = extract_pdf_text(url)

        rows.append({
            "company": company,
            "url": url,
            "scope1": "",
            "scope2": "",
            "scope3": "",
            "renewable_energy": "",
            "raw_info": text
        })

    # Save results to CSV
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"\n✅ Done! Extracted data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
