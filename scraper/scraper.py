import pandas as pd
import requests
from PyPDF2 import PdfReader
from io import BytesIO
import re

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
        for page in pdf.pages[:10]:  # check first 10 pages
            text.append(page.extract_text() or "")

        return "\n".join(text).strip()

    except Exception as e:
        return f"Error extracting PDF: {e}"


def parse_esg_data(text: str) -> dict:
    """Extract Scope 1/2/3 emissions and renewable energy values using regex."""

    def search_pattern(patterns):
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    # Pattern explanation:
    # - ([\d,]+\.?\d*) → number like 12,345.67
    # - (?:\s*(?:tCO2e?|MTCO2|million tonnes|tons|tC[O₂2]))? → optional units
    num_with_units = r"([\d,]+\.?\d*\s*(?:tCO2e?|MTCO2|million tonnes|tons|tCO2|tC[O₂2])?)"

    scope1 = search_pattern([
        rf"Scope\s*1[^0-9]*{num_with_units}",
        rf"Scope\s*I[^0-9]*{num_with_units}",
    ])

    scope2 = search_pattern([
        rf"Scope\s*2[^0-9]*{num_with_units}",
        rf"Scope\s*II[^0-9]*{num_with_units}",
    ])

    scope3 = search_pattern([
        rf"Scope\s*3[^0-9]*{num_with_units}",
        rf"Scope\s*III[^0-9]*{num_with_units}",
    ])

    renewable = search_pattern([
        r"Renewable\s*Energy[^0-9]*([\d,]+\.?\d*\s*%?)",
        r"Renewables[^0-9]*([\d,]+\.?\d*\s*%?)",
        r"Green\s*Power[^0-9]*([\d,]+\.?\d*\s*%?)",
    ])

    return {
        "scope1": scope1,
        "scope2": scope2,
        "scope3": scope3,
        "renewable_energy": renewable,
    }


def main():
    rows = []

    for entry in COMPANIES:
        company = entry["company"]
        url = entry["url"]

        print(f"Processing {company}...")
        text = extract_pdf_text(url)

        if text.startswith("Error"):
            data = {
                "company": company,
                "url": url,
                "scope1": "",
                "scope2": "",
                "scope3": "",
                "renewable_energy": "",
                "raw_info": text,
            }
        else:
            parsed = parse_esg_data(text)
            data = {
                "company": company,
                "url": url,
                **parsed,
                "raw_info": text[:2000],  # limit for readability
            }

        rows.append(data)

    # Save results to CSV
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"\n✅ Done! Extracted data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
