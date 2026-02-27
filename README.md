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
Auto-detects the first supported file (PDF, JPG, PNG) in `data/input/` and outputs JSON + Markdown to `data/output/`:

```bash
# Extract with schema (default)
python -m src.main

# Extract without schema enforcement
python -m src.main --no-schema

# Custom output paths (optional)
python -m src.main --out data/output/custom.json --out-md data/output/custom.md
```

## Streamlit Apps

### 1. Document Extraction App
Batch process documents with OCR and LLM extraction:

```bash
streamlit run app.py
```

**Features:**
- **Document Selection**: Upload a folder path (e.g., `data/input`) with PDFs/images
- **Schema Toggle**: Enforce structured output or extract freely
- **Results Tabs:**
  - **Markdown**: Extracted fields with OCR confidence scores
  - **JSON**: Structured output  
  - **Raw OCR Output**: All detected text with confidence scores
  - **OCR Visualization**: Bounding boxes and confidence overlaid on images
- Auto-saves results to `data/output/`

### 2. Loan Qualification Checker App
Assess borrower eligibility using financial documents:

```bash
streamlit run loan_checker.py
```

**Features:**
- Upload 3 financial documents: pay stub, bank statement, investment statement
- Calculate 3 approval metrics:
  1. **Payment-to-Income Ratio** - Monthly Payment / Net Income
  2. **Disposable Income** - Income - (Expenses + Monthly Payment)
  3. **Liquidity vs Payment** - Liquid Assets / Monthly Payment
- Get overall qualification assessment (Likely to Qualify / Conditional Approval / High Risk)

### 3. RAG Search Interface
Query your indexed documents by semantic meaning:

```bash
streamlit run RAG/search.py
```

**Features:**
- **Build Index**: Select documents and create FAISS vector index
- **Semantic Search**: Find documents by meaning (e.g., "receipts from Walmart")
- **Filters**: Search by document type with relevance scoring
- **Chat Q&A**: Ask questions and get answers grounded in your documents
- **Source Citations**: See which documents contributed to each answer

### Extraction Modes (CLI)

**With Schema (default)** - Enforces structured output for: pay_stub, bank_statement, investment_statement, receipt
```bash
python -m src.main
```

**Without Schema** - Extracts all detected fields freely:
```bash
python -m src.main --no-schema
```

## RAG Storage for Downstream Processing

The system supports storing extracted documents in a **RAG (Retrieval Augmented Generation)** vector store for semantic search and intelligent document retrieval.

### What is RAG?

RAG enables you to:
- **Semantic Search**: Find documents by meaning, not just keywords
- **Metadata Filtering**: Filter by document type, confidence scores, dates, etc.
- **Downstream Processing**: Build analytics pipelines and AI workflows
- **Context Retrieval**: Get relevant chunks with surrounding context

### Quick Start

#### 1. Index Documents
After extracting documents with `app.py`:
```bash
python -m rag_indexing.build_index
```

This reads JSON from `data/output/` and builds a FAISS index in `faiss_index/` (uses `vectordb_client.py`).

#### 2. Search Documents
Open the RAG Search app to query your index:
```bash
streamlit run RAG/search.py
```

#### 3. Example Usage

For programmatic usage examples, see:
- [examples/example_rag_usage.py](examples/example_rag_usage.py) - Search patterns and filtering




