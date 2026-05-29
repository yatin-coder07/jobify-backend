import fitz


class PDFParser:

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        doc = fitz.open(pdf_path)

        full_text = []

        for page in doc:
            text = page.get_text()
            full_text.append(text)

        return "\n".join(full_text)