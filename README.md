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

4. Uncomment the data folder rule in `.gitignore` so `data/` is included:

```bash
# Change this:
# data/

# To this:
data/
```

## Run
Run with any input/output file:

```bash
# Works with any filename and supported format (PDF, JPG, PNG)
python -m src.main data/input/any_filename.pdf --out data/output/any_output.json
python -m src.main data/input/any_filename.jpg --out data/output/any_output.json
python -m src.main data/input/any_filename.png --out data/output/any_output.json
```

This will also write a Markdown summary next to the JSON (same name, .md extension). You can override it:

```bash
python -m src.main data/input/any_filename.pdf --out data/output/any_output.json --out-md data/output/any_output.md
```

Or run with auto-detection (automatically finds the first file in `data/input/`):

```bash
python -m src.main
python -m src.main --no-schema
```

### Extraction Modes

**With Schema (default)** - Enforces one of these document schemas:

- pay_stub: employee_name, pay_period, gross_pay, net_pay
- bank_statement: bank_name, account_number, balance
- investment_statement: investment_year, total_investment, changes_in_value

```bash
python -m src.main data/input/document.pdf
```

Output will always have this structure (numeric fields are numbers):
```json
{
  "document_type": "pay_stub | bank_statement | investment_statement",
  "fields": {
    "...": "..."
  }
}
```

**Without Schema** - Extracts all text/fields freely without enforcing the fixed schema:
```bash
python -m src.main data/input/document.pdf --no-schema
```

This mode extracts any field it finds and returns them dynamically.
