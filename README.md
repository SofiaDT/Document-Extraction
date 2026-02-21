# Document Extraction (PDF -> LLM -> JSON)

## Setup
1. Install deps:

```bash
pip install -r requirements.txt
```

2. Create `.env` and set your key:

```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1
```

## Run
Run with explicit input/output:

```bash
python -m src.main data/input/your.pdf --out data/output/your.json
```

Or run with defaults (uses `data/input/AI Implementation Manager job in London _ Wise.pdf` and writes to `data/output/extraction.json`):

```bash
python -m src.main
```