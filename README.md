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

### Authentication
All Streamlit apps require login. Default credentials:

**User 1:**
- Username: `admin`
- Password: `admin123`

**User 2:**
- Username: `demo`
- Password: `demo123`

To customize users, edit `config.yaml` and modify the `credentials.usernames` section.

### 1. Document Extraction App
Batch process documents with OCR and LLM extraction:

```bash
streamlit run apps/document_extraction.py
```

**Features:**
- **Login Screen**: Secure access with username/password
- **Session Timeout**: Auto-logout after 30 minutes of inactivity
- **Document Selection**: Upload a folder path (e.g., `data/input`) with PDFs/images
- **Schema Toggle**: Enforce structured output or extract freely
- **Results Tabs:**
  - **Markdown**: Extracted fields with OCR confidence scores
  - **JSON**: Structured output  
  - **Raw OCR Output**: All detected text with confidence scores
  - **OCR Visualization**: Bounding boxes and confidence overlaid on images
- Auto-saves results to `data/output/`
- **Logout**: Available in the sidebar when logged in
- **💬 Chat with Your Documents**: Ask natural language questions to search and get insights from all extracted documents using LLM
- **Audit Logging**: All user actions recorded for compliance

### 2. Loan Qualification Checker App
Assess borrower eligibility using financial documents:

```bash
streamlit run apps/loan_checker.py
```

**Features:**
- **Login Authentication**: Secure access with username/password
- **Session Timeout**: Auto-logout after 30 minutes of inactivity
- Upload 3 financial documents: pay stub, bank statement, investment statement
- Calculate 3 approval metrics:
  1. **Payment-to-Income Ratio** - Monthly Payment / Net Income
  2. **Disposable Income** - Income - (Expenses + Monthly Payment)
  3. **Liquidity vs Payment** - Liquid Assets / Monthly Payment
- Get overall qualification assessment (Likely to Qualify / Conditional Approval / High Risk)
- **Review & Approve**: Manually review metrics before saving to dashboard
- **Automatic Tracking**: All approved applications are logged for dashboard analytics
- **Audit Logging**: All user actions (login, logout, approvals) are recorded for compliance
- **PII Protection**: Personal information is redacted in audit trails

**Note:** Loan application data is stored in `data/output/loan_applications.json` alongside extracted documents. Audit logs are stored in `data/output/audit_log.json`.

**Security Features:**
- Session-based authentication with configurable timeout
- PII redaction in logs and audit trails
- Audit event logging for all user actions
- Optional encryption-at-rest for sensitive data (see Data Security section)

### 3. Loan Processing Dashboard
Real-time analytics and productivity metrics for loan applications:

```bash
streamlit run apps/loan_dashboard.py
```

**Features:**
- **Login Authentication**: Secure access with username/password
- **Session Timeout**: Auto-logout after 30 minutes of inactivity
- **Volume & Throughput Metrics**: Total applications, average processing time, approval rates
- **Qualification Insights**: Distribution pie chart, financial metrics analysis
- **Processing Timeline**: Applications over time with trend visualization
- **Document Quality**: Average OCR confidence scores by document type
- **Peak Hours Analysis**: Identify when most applications are processed
- **Team Performance**: Individual user statistics and processing rates
- **Financial Metrics Breakdown**: Payment ratios, disposable income, liquidity analysis
- **Recent Applications Table**: Last 10 applications with key details (applicants redacted for privacy)
- **CSV Export**: Download complete analytics data (with PII redacted)
- **Audit Logging**: All dashboard access and views recorded for compliance
- **PII Protection**: Applicant names are redacted in all displays and exports

**Note:** Dashboard automatically shows data from applications processed in the Loan Checker app. Applicant identities are protected through PII redaction.

### 4. RAG Search Interface
Query your indexed documents by semantic meaning:

```bash
streamlit run apps/rag_search.py
```

**Features:**
- **Login Authentication**: Secure access with username/password
- **Session Timeout**: Auto-logout after 30 minutes of inactivity
- **Build Index**: Select documents and create FAISS vector index
- **Semantic Search**: Find documents by meaning (e.g., "receipts from Walmart")
- **Filters**: Search by document type with relevance scoring
- **Chat Q&A**: Ask questions and get answers grounded in your documents
- **Source Citations**: See which documents contributed to each answer
- **Audit Logging**: All user actions recorded for compliance

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
After extracting documents with the Document Extraction app:
```bash
python -m rag_indexing.build_index
```

This reads JSON from `data/output/` and builds a FAISS index in `faiss_index/` (uses `vectordb_client.py`).

#### 2. Search Documents
Open the RAG Search app to query your index:
```bash
streamlit run apps/rag_search.py
```

**Note:** All RAG operations now use a single `/faiss_index` directory at the project root for consistency.

#### 3. Example Usage

For programmatic usage examples, see:
- [examples/example_rag_usage.py](examples/example_rag_usage.py) - Search patterns and filtering

## Data Security & Privacy

This system includes built-in security features for protecting sensitive financial and personal information:

### Authentication & Session Management

- **Username/Password Login**: All Streamlit apps require authentication
- **Session Timeout**: Auto-logout after 30 minutes of inactivity (configurable)
- **Secure Credentials**: Stored in `apps/config.yaml` (add to `.gitignore` in production)

### Audit Logging

All user actions are recorded for compliance and security auditing:

```bash
# View audit logs
cat data/output/audit_log.json
```

**Logged Events:**
- User login/logout attempts (including failed attempts)
- Application approvals with timestamp and qualification decision
- Access to sensitive resources

Example audit entry:
```json
{
  "timestamp": "2026-03-02T15:00:00.000000",
  "username": "admin",
  "action": "approved_application",
  "resource": "APP-20260302-145101-1",
  "status": "success",
  "details": {
    "qualification": "High Risk",
    "applicant_partial": "***RYAN"
  }
}
```

### PII Protection

- **Redaction in Logs**: Personal identifiable information (names, SSNs, account numbers) is redacted in audit trails
- **Partial Name Retention**: Only last 3 characters of applicant names displayed in audit logs for verification
- **No Sensitive Data in Error Messages**: Error logs never contain passwords, API keys, or financial details

### Encryption (Optional)

For production deployments, you can encrypt sensitive data at rest:

```python
from apps.encryption import encrypt_file, decrypt_file
from pathlib import Path

# Encrypt the loan applications file
encrypt_file(Path("data/output/loan_applications.json"))

# Later, decrypt when needed
data = decrypt_file(Path("data/output/loan_applications.json"))
```

**Encryption Details:**
- Uses Fernet symmetric encryption (256-bit AES)
- Encryption key stored in `data/output/.encryption_key` (add to `.gitignore`)
- Backups created before encryption (`.json_backup`)
- In production, store encryption key in a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)

### Compliance Considerations

**Fair Lending Laws:**
- System calculates approval metrics based on financial metrics only
- Ensure no protected characteristics (race, gender, age, etc.) influence decisions
- Document decision criteria and audit trails for regulatory compliance

**Data Residency:**
- All files stored locally in `data/` directory
- Configure your hosting environment for required data residency (GDPR, CCPA, etc.)
- Consider backup and disaster recovery procedures

**Third-Party Services:**
- OpenAI API: Review their privacy policy for LLM data handling
- FAISS: Runs locally, no external data transmission
- Streamlit: Check their privacy policy for session data

### Recommended Production Setup

1. **Environment Variables**: Use `.env` for all secrets (API keys, database URLs)
2. **Encryption**: Enable encryption-at-rest for all JSON data files
3. **Audit Logging**: Regularly archive and analyze audit logs
4. **Access Controls**: Implement role-based access (loan officer, admin, auditor)
5. **Backup Strategy**: Regular encrypted backups with off-site storage
6. **Security Updates**: Keep dependencies updated (`pip list --outdated`)
7. **Monitoring**: Log all critical events and set up alerts for suspicious activity




