"""
Synthetic PDF Generator for KnowledgeMesh test cases.
Generates test documents covering:
1. Corroboration (Doc 1 vs Doc 2)
2. Genuine Contradiction (Doc 1 vs Doc 3)
3. Apparent Contradiction / Reconciliation (Doc 1 vs Doc 4)
4. Extraction Failure / Noise Rejection (Doc 5)
5. Out-of-Domain Technical Specs (Doc 6)
6. Large Multi-Page Document (Doc 7)
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

SAMPLE_DIR = Path(__file__).resolve().parent

def create_pdf(filename: str, pages_content: list[list[str]], title: str):
    pdf_path = SAMPLE_DIR / filename
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=12
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#334155'),
        spaceAfter=10
    )

    story = []
    for page_idx, page_paras in enumerate(pages_content):
        if page_idx == 0:
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
        for para_text in page_paras:
            story.append(Paragraph(para_text, body_style))
            story.append(Spacer(1, 8))
        if page_idx < len(pages_content) - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"Generated {pdf_path.name} ({len(pages_content)} pages)")
    return pdf_path

def generate_all_samples():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Doc 1: Financial Report FY24
    create_pdf(
        "doc1_annual_report_fy24.pdf",
        [[
            "Annual Financial Report for Acme Logistics",
            "Acme Logistics reported revenue of Rs. 2,500 crore in FY2024.",
            "Acme Logistics achieved EBITDA of Rs. 350 crore in FY2024.",
            "The company recorded net profit of Rs. 180 crore in FY2024."
        ]],
        "Acme Logistics — Annual Report FY2024"
    )

    # 2. Doc 2: Investor Deck FY24 (Corroboration)
    create_pdf(
        "doc2_investor_deck_fy24.pdf",
        [[
            "Investor Presentation — Fiscal Year Performance",
            "Acme Logistics reported revenue of Rs. 2,500 crore in FY2024.",
            "Operating profitability was strong with EBITDA of Rs. 350 crore in FY2024."
        ]],
        "Acme Logistics — Investor Presentation FY2024"
    )

    # 3. Doc 3: Press Release (Contradiction)
    create_pdf(
        "doc3_conflicting_press_release.pdf",
        [[
            "Press Release: Erroneous Publication",
            "Acme Logistics reported revenue of Rs. 3,200 crore in FY2024.",
            "The company noted robust expansion across all enterprise sectors."
        ]],
        "Acme Logistics — Media Briefing FY2024"
    )

    # 4. Doc 4: Quarterly Statement Q1 (Reconciliation)
    create_pdf(
        "doc4_quarterly_statement_q1.pdf",
        [[
            "First Quarter Financial Results",
            "Acme Logistics recorded revenue of Rs. 650 crore in Q1 FY2024.",
            "Quarterly operational volume expanded by 12% year-on-year."
        ]],
        "Acme Logistics — Q1 FY2024 Statement"
    )

    # 5. Doc 5: Noisy Document (Extraction Failure / Noise Rejection)
    create_pdf(
        "doc5_noisy_document.pdf",
        [[
            "Statistical Appendix and Random Tabulations",
            "4 FY23",
            "Page 42",
            "Section • 4",
            "Index 99",
            "Unrelated numerical footnotes without predicate: 15."
        ]],
        "Appendix Notes and Fragmented Data"
    )

    # 6. Doc 6: Technical Manual (Out-of-Domain Generalization)
    create_pdf(
        "doc6_coffee_machine_manual.pdf",
        [[
            "DeLonghi Magnifica Technical User Manual",
            "The DeLonghi Magnifica features a water tank capacity of 1.8 liters.",
            "The machine operates with an operating pressure of 15 bar.",
            "Power consumption is rated at 1450 watts."
        ]],
        "DeLonghi Magnifica Espresso Machine Specifications"
    )

    # 7. Doc 7: Multi-page Document (Large PDF Chunking & Page Tracking)
    large_pages = []
    for p in range(1, 11):
        if p == 2:
            content = [
                f"Page {p} Executive Summary.",
                "Apex Systems achieved revenue of $500 million in FY2024.",
                "Market share reached 24% across enterprise software clients."
            ]
        elif p == 6:
            content = [
                f"Page {p} Operational Review.",
                "Apex Systems recorded net profit of $65 million in FY2024.",
                "Cloud division demonstrated high customer retention."
            ]
        elif p == 9:
            content = [
                f"Page {p} Outlook and Forward Metrics.",
                "Apex Systems projected revenue of $600 million in FY2025."
            ]
        else:
            content = [
                f"Page {p} Administrative section and background disclosures.",
                "Standard regulatory commentary and general procedural text without specific financial claims."
            ]
        large_pages.append(content)

    create_pdf(
        "doc7_large_annual_report.pdf",
        large_pages,
        "Apex Systems Comprehensive Multi-Page Review"
    )

if __name__ == "__main__":
    generate_all_samples()
