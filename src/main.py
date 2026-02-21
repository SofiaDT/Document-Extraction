import argparse
import json
from pathlib import Path

from .config import get_openai_settings
from .llm_extract import extract_key_values
from .pdf_extract import extract_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract structured data from a PDF.")
    parser.add_argument(
        "input_pdf",
        nargs="?",
        default="data/input/AI Implementation Manager job in London _ Wise.pdf",
        help="Path to the input PDF.",
    )
    parser.add_argument(
        "--out",
        dest="output_json",
        default="data/output/extraction.json",
        help="Path to the output JSON file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_pdf = Path(args.input_pdf)
    output_json = Path(args.output_json)

    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")

    api_key, model = get_openai_settings()

    text = extract_text(input_pdf)
    if not text:
        raise RuntimeError("No text extracted. If the PDF is scanned, you'll need OCR later.")

    result = extract_key_values(api_key, model, text)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {output_json}")


if __name__ == "__main__":
    main()