from pathlib import Path
import pymupdf


def extract_text(pdf_path: Path) -> str:
    doc = pymupdf.open(str(pdf_path))
    parts = []

    for page in doc:
        txt = page.get_text("text") or ""
        if txt.strip():
            parts.append(txt)

    return "\n\n".join(parts).strip()