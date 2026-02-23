import argparse
import json
from pathlib import Path

from .config import get_openai_settings
from .llm_extract import extract_key_values
from .pdf_extract import extract_text
from .image_extract import extract_text_from_image


def get_file_type(file_path: Path) -> str:
    """Determine file type from extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    elif suffix in [".jpg", ".jpeg", ".png"]:
        return "image"
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: PDF, JPG, PNG")


def extract_document_text(file_path: Path) -> str:
    """Extract text from document (PDF or image) based on file type."""
    file_type = get_file_type(file_path)
    
    if file_type == "pdf":
        return extract_text(file_path)
    elif file_type == "image":
        return extract_text_from_image(file_path)


def get_input_file() -> Path:
    """Get input file from argument or auto-detect from data/input directory."""
    args = parse_args()
    
    # If a file was explicitly provided, use it
    if args.input_file != "data/input/AI Implementation Manager job in London _ Wise.pdf":
        return Path(args.input_file)
    
    # Try to auto-detect a file in data/input
    input_dir = Path("data/input")
    if input_dir.exists():
        supported_files = []
        for ext in ["*.pdf", "*.jpg", "*.jpeg", "*.png"]:
            supported_files.extend(input_dir.glob(ext))
        
        if supported_files:
            input_file = supported_files[0]
            print(f"Auto-detected input file: {input_file}")
            return input_file
    
    # Fall back to default
    return Path(args.input_file)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract structured data from a document (PDF, JPG, PNG).")
    parser.add_argument(
        "input_file",
        nargs="?",
        default="data/input/AI Implementation Manager job in London _ Wise.pdf",
        help="Path to the input file (PDF, JPG, or PNG). If not provided, auto-detects any file in data/input/.",
    )
    parser.add_argument(
        "--out",
        dest="output_json",
        default="data/output/extraction.json",
        help="Path to the output JSON file.",
    )
    parser.add_argument(
        "--no-schema",
        action="store_true",
        help="Extract all text without enforcing the fixed insurance schema.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_file = get_input_file()
    output_json = Path(args.output_json)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    api_key, model = get_openai_settings()

    text = extract_document_text(input_file)
    if not text:
        raise RuntimeError("No text extracted from document.")

    result = extract_key_values(api_key, model, text, enforce_schema=not args.no_schema)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {output_json}")


if __name__ == "__main__":
    main()