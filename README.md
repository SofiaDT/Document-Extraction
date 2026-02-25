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

## Streamlit App
Run the UI for batch processing a folder with schema selection:

1. Start the Streamlit server:
```bash
streamlit run app.py
```

2. The app will open in your browser (usually `http://localhost:8501`).

3. **Document Selection Tab:**
   - Enter the path to a folder containing your documents (e.g., `data/input`)
   - Check/uncheck "Use schema" to enforce schema validation or extract freely
   - Click **Begin Extraction** to process all supported files (.pdf, .jpg, .jpeg, .png)

4. **Results Tab:**
   - View JSON, Markdown, and raw extracted text for each processed document
   - Files are automatically saved to `data/output/`

5. Click **Reset** anytime to clear all results and start over.

### Extraction Modes

**With Schema (default)** - Enforces one of these document schemas:

- pay_stub: employee_name, pay_period, gross_pay, net_pay
- bank_statement: bank_name, account_number, balance
- investment_statement: customer_name, investment_year, beginning_value, ending_value

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
