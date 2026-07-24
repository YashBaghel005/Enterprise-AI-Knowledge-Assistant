import fitz

class PDFService:
    def extract_text(self, pdf_path: str):
        pages = []
        document = fitz.open(pdf_path)

        for page_number, page in enumerate(document, start=1):

            text = page.get_text().strip()
            if text:
                pages.append(
                    {
                        "page_number": page_number,
                        "text": text,
                    }
                )

        document.close()
        return pages