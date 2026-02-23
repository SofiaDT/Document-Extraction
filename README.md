# Document Extraction (PDF/JPG/PNG -> OCR -> LLM -> JSON)

## Setup
1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env` and set your key:

```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1
```

3. Create the data folder structure:

```bash
mkdir -p data/input data/output
```

## Run
Run with any input/output file:

```bash
# Works with any filename and supported format (PDF, JPG, PNG)
python -m src.main data/input/any_filename.pdf --out data/output/any_output.json
python -m src.main data/input/any_filename.jpg --out data/output/any_output.json
python -m src.main data/input/any_filename.png --out data/output/any_output.json
```

Or run with auto-detection (automatically finds the first file in `data/input/`):

```bash
python -m src.main
```

### Extraction Modes

**With Schema (default)** - Enforces the fixed insurance invoice schema with all required fields:
```bash
python -m src.main data/input/document.pdf
```

Output will always have this structure:
```json
{
  "document_type": "insurance_invoice",
  "fields": {
    "insurance_company": "...",
    "invoice_number": "...",
    "balance_due_company": "...",
    ...
  }
}
```

**Without Schema** - Extracts all text/fields freely without enforcing the fixed schema:
```bash
python -m src.main data/input/document.pdf --no-schema
```

This mode extracts any field it finds and returns them dynamically.
