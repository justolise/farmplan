from typing import List  # noqa: UP035

import PyPDF2


def extract_text_from_pdf(pdf_path: str) -> List[str]:
    """Extracts text from a PDF file and returns a list of pages."""
    text_pages = []
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text_pages.append(page.extract_text())
    except Exception as e:  # noqa: BLE001
        print(f"Error reading PDF {pdf_path}: {e}")
    return text_pages
