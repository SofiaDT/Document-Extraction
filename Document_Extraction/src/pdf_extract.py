from pathlib import Path
import pymupdf


def _ocr_pdf(doc: pymupdf.Document) -> str:
    import numpy as np
    import easyocr

    reader = easyocr.Reader(["en"], gpu=False)
    parts = []

    for page in doc:
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        channels = pix.n
        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, channels)
        if channels == 4:
            image = image[:, :, :3]

        lines = reader.readtext(image, detail=0)
        if lines:
            parts.append("\n".join(lines))

    return "\n\n".join(parts).strip()


def extract_text(pdf_path: Path) -> str:
    doc = pymupdf.open(str(pdf_path))
    parts = []

    for page in doc:
        txt = page.get_text("text") or ""
        if txt.strip():
            parts.append(txt)

    text = "\n\n".join(parts).strip()
    if text:
        return text

    print("No embedded text found in PDF. Running OCR...")
    return _ocr_pdf(doc)