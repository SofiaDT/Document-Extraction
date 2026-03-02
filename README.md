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
- **Start Over - Failed Application Tracking**: When clicking "Start Over", you'll be prompted to select a failure reason:
  - Missing data or documents
  - Invalid or inconsistent data
  - Insufficient income/funds
  - Poor document quality
  - Other reason
  - The failed application is automatically logged with your selected reason for analysis
- **Automatic Tracking**: All approved and failed applications are logged for dashboard analytics
- **Audit Logging**: All user actions (login, logout, approvals, failures) are recorded for compliance
- **PII Protection**: Personal information is redacted in audit trails

**Note:** Loan application data (both approved and failed) is stored in `data/output/loan_applications.json` alongside extracted documents. Audit logs are stored in `data/output/audit_log.json`.

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

## Cost & Efficiency Tracking

The loan processing system tracks AI infrastructure costs and calculates efficiency metrics to optimize spending and measure ROI.

### Dashboard Cost Metrics

The **Loan Processing Dashboard** includes a dedicated **Cost & Efficiency Metrics** section that displays:

#### Real-Time Cost Tracking
- **Total Spend**: Cumulative cost across all processed applications
- **Monthly Spend**: Current month's AI infrastructure costs
- **Spend Alerts**: Red warning flag if monthly spend exceeds budget threshold ($100)

#### Efficiency Metrics
- **Cost Per Approval**: Average cost to approve each application
- **Hours Saved**: Total hours saved vs. manual document review (assumes 30 min manual review)
- **Cost Per Hour Saved**: Efficiency metric showing cost to save one hour of manual labor
- **Estimated ROI**: Return on investment assuming $50/hour labor cost

#### Cost Analysis Charts
1. **Daily Cost Trend**: Line chart showing cost evolution over time
2. **Daily Token Usage**: Bar chart tracking API token consumption
3. **Cost by Qualification**: Box plot comparing costs across different approval outcomes
4. **Processing Time vs Cost**: Scatter plot with trend line showing latency correlation

### How Costs Are Calculated

#### Token Counting
The system uses `tiktoken` library to count tokens for:
- **Input**: Extracted text from documents + prompt overhead
- **Output**: LLM structured extraction response

```python
from cost_tracking import count_tokens, estimate_cost

# Count tokens from extracted document text
input_tokens = count_tokens("John Doe earned $5,000...", "gpt-4")

# Estimate cost (GPT-4: $0.03/1K input, $0.06/1K output)
cost = estimate_cost(input_tokens=500, output_tokens=200, model="gpt-4")
print(f"Total cost: ${cost['total_cost']:.4f}")
```

#### Supported Models & Pricing
- **gpt-4**: $0.03 per 1K input tokens, $0.06 per 1K output tokens
- **gpt-4-turbo**: $0.01 per 1K input tokens, $0.03 per 1K output tokens  
- **gpt-3.5-turbo**: $0.0005 per 1K input tokens, $0.0015 per 1K output tokens

#### Hours Saved Calculation
```
Hours Saved = (Manual Review Time - Processing Time) / 3600 seconds
            = (30 minutes - actual processing seconds) / 3600
```

For example:
- Manual document review: 30 minutes per application
- Actual processing: 45 seconds
- Hours saved: (30*60 - 45) / 3600 = **0.49 hours**

### Cost Tracking in Loan Checker

When you approve an application in the **Loan Checker** app:

1. **Token counting**: System counts tokens from all extracted text and structured data
2. **Cost estimation**: Calculates cost using OpenAI pricing for GPT-4
3. **Application logging**: Saves application with cost data to `data/output/loan_applications.json`

Example logged record:
```json
{
  "application_id": "APP-20260302-145101-1",
  "timestamp": "2026-03-02T14:51:01.000000",
  "applicant_name": "John Doe",
  "input_tokens": 512,
  "output_tokens": 287,
  "cost_usd": 0.02295,
  "processing_time_seconds": 3.2,
  "qualification": "Likely to Qualify"
}
```

### Cost Metrics API

Use the cost tracking module programmatically:

```python
from cost_tracking import (
    count_tokens,
    estimate_cost,
    calculate_hours_saved,
    get_cost_per_approval,
    get_cost_per_hour_saved
)
from loan_tracking import get_cost_metrics

# Get comprehensive cost statistics
metrics = get_cost_metrics()
print(f"Total cost: ${metrics['total_cost']:.2f}")
print(f"Total tokens: {metrics['total_tokens']}")
print(f"Total approvals: {metrics['approvals']}")
print(f"Cost per approval: ${metrics['cost_per_approval']:.2f}")
print(f"Hours saved: {metrics['total_hours_saved']:.1f}h")
print(f"Cost per hour saved: ${metrics['cost_per_hour_saved']:.2f}")
```

### Optimization Tips

1. **Reduce Token Usage**
   - Use templates to extract only necessary fields
   - Pre-process documents to remove irrelevant pages
   - Consider GPT-3.5-turbo for simple extractions (90% cheaper)

2. **Batch Processing**
   - Process multiple applications together during off-peak hours
   - Implement job queues to manage API rate limits

3. **Quality vs Cost Tradeoff**
   - Monitor confidence scores alongside costs
   - Higher confidence documents may need fewer retries

4. **Monitor Spend**
   - Dashboard alerts warn when monthly spend exceeds budget
   - Export CSV reports for cost analysis and forecasting

### Testing Cost Tracking

Run the cost tracking test suite:

```bash
python test_cost_tracking.py
```

This validates:
- Token counting accuracy
- Cost estimation calculations
- Hours saved metrics
- Cost aggregation functions
- Dashboard metric retrieval

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
8. **Cost Monitoring**: Set monthly spend budgets and investigate unusual spikes




