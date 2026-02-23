from pathlib import Path
import easyocr


def extract_text_from_image(image_path: Path) -> str:
    """Extract text from image (JPG, PNG) using OCR."""
    try:
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(str(image_path))
        text = '\n'.join([item[1] for item in results])
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from image {image_path}: {e}")
