# Changelog

All notable changes to the Document Extraction and Loan Processing system are documented in this file.

## [Unreleased]

### Added

#### Failed Application Tracking
- **Start Over with Logging**: When clicking "Start Over" in Loan Checker, users now select a failure reason:
  - Missing data or documents
  - Invalid or inconsistent data
  - Insufficient income/funds
  - Poor document quality
  - Other reason (with optional notes)
- **Failed Application Records**: All failed applications logged to `loan_applications.json` with:
  - `status: "failed"`
  - `failure_reason`: Selected reason from above
  - `notes`: Additional details if provided
  - `application_id`: Format "APP-YYYYMMDD-HHMMSS-FAILED-N"
- **Audit Trail**: Failed applications recorded in audit logs with applicant PII redacted
- **New Function**: `log_failed_application()` in loan_tracking.py for programmatic access

#### Cost & Efficiency Tracking
- **Token Counting**: Integrated `tiktoken` for accurate token counting on all extracted documents
- **Cost Estimation**: Automated cost calculation based on OpenAI pricing models (GPT-4, GPT-4-turbo, GPT-3.5-turbo)
- **Hours Saved Metrics**: Track time savings vs. manual document review (30-min baseline)
- **Cost Per Approval**: Calculate average cost per successful loan approval
- **ROI Calculation**: Estimate return on investment using labor cost metrics

#### Dashboard Cost Metrics Section
- Total spend tracking across all applications
- Monthly burn rate with budget threshold alerts ($100 default)
- Cost distribution charts (cost by qualification, processing time vs cost scatter plot)
- Daily cost trend visualization
- Daily token usage bar chart
- Efficiency metrics cards:
  - Cost per approval
  - Hours saved
  - Cost per hour saved
  - Estimated ROI

#### New Files
- `apps/cost_tracking.py`: Core cost calculation module
  - `count_tokens(text, model)`: Token counting for text
  - `estimate_cost(input_tokens, output_tokens, model)`: Cost calculation
  - `calculate_hours_saved(processing_time_seconds, manual_review_minutes)`: Efficiency metric
  - `get_cost_per_approval(total_cost, approvals)`: Per-approval cost
  - `get_cost_per_hour_saved(total_cost, total_hours_saved)`: Efficiency ratio

- `test_cost_tracking.py`: Comprehensive test suite for cost tracking functionality

#### Loan Tracking Enhancements
- Updated `log_application()` signature to accept:
  - `input_tokens`: Tokens used for document extraction
  - `output_tokens`: Tokens used for LLM response
  - `cost_usd`: Total cost for the approval
- New aggregation functions in `loan_tracking.py`:
  - `get_total_cost()`: Cumulative spending
  - `get_monthly_cost(year, month)`: Period-based spending
  - `get_cost_metrics()`: Comprehensive metrics dictionary with 10+ fields

#### Loan Checker Integration
- Token counting for all extracted documents before approval
- Cost estimation on approval button click
- Automatic passing of cost data to loan application logging

#### Documentation
- Comprehensive Cost & Efficiency Tracking section in README.md
- Usage examples for cost tracking API
- Optimization tips for reducing token usage and costs
- Production setup recommendations for cost monitoring

### Modified
- `apps/loan_checker.py`: 
  - Added cost_tracking import and token counting/cost estimation before approval
  - Added failed application tracking with user-selectable failure reasons
  - "Start Over" button now logs failed applications before clearing form
  - Added session state management for failure form display
- `apps/loan_tracking.py`:
  - Added `log_failed_application()` function for tracking application failures
- `apps/loan_dashboard.py`: 
  - Added get_cost_metrics import
  - Added Cost & Efficiency Metrics section with 7+ visualizations
  - Added spend alert logic
  - Added ROI calculations
- `README.md`: 
  - Added extensive Cost & Efficiency Tracking documentation
  - Documented "Start Over" failure tracking feature in Loan Checker section

### Fixed
- Session timeout logic properly applied across all 4 Streamlit apps
- PII redaction consistently applied in audit logs and dashboard displays
- Loan applications data structure now includes cost tracking fields
- Failed applications now tracked with audit logging for analysis

## [Previous Changes]

### Authentication & Session Management (Earlier)
- Added login authentication to all Streamlit apps
- Implemented 30-minute session timeout with logout audit logging
- Session state management for secure user tracking

### PII Protection & Audit Logging (Earlier)
- Implemented PII redaction for sensitive data
- Added comprehensive audit event logging
- Optional encryption-at-rest using Fernet (256-bit AES)

### Dashboard & Analytics (Earlier)
- Built comprehensive Loan Processing Dashboard
- Qualification distribution and financial metrics analysis
- Team performance and processing time analytics
- Document confidence scoring visualization
- Recent applications table with PII redaction

### Data Organization (Earlier)
- Consolidated data storage to single `data/output/` directory
- Unified FAISS index location at `/faiss_index`
- Cleaned up loan_applications.json (removed stale test records)

---

## Deployment & Testing

### Running Tests
```bash
python test_cost_tracking.py
```

Expected output:
- ✅ Token counting (sample text = 16 tokens)
- ✅ Cost estimation ($0.0270 for GPT-4 test case)
- ✅ Hours saved calculation (0.49 hours for 45-second processing)
- ✅ Cost per metric calculations
- ✅ Aggregated metrics retrieval

### Dashboard Access
1. Start dashboard: `streamlit run apps/loan_dashboard.py`
2. Login with `admin` / `admin123`
3. Process applications in Loan Checker app to populate cost metrics
4. Approve applications to see cost tracking in dashboard

### Cost API Usage
```python
from cost_tracking import count_tokens, estimate_cost
from loan_tracking import get_cost_metrics

# Count tokens in sample text
tokens = count_tokens("Sample loan application text...", "gpt-4")

# Estimate cost
cost = estimate_cost(tokens, 200, "gpt-4")

# Get dashboard metrics
metrics = get_cost_metrics()
print(f"Total spend: ${metrics['total_cost']:.2f}")
```

---

## Known Limitations

- Cost tracking begins only after integration is deployed
- Historical applications without cost data show $0.00 cost
- Token counting estimates assume GPT-4 encoding (may vary slightly between models)
- ROI calculation assumes $50/hour labor cost (configurable in dashboard)

## Future Enhancements

- [ ] Database-backed cost history for better analytics
- [ ] Cost forecasting based on historical trends
- [ ] Model selection optimization based on cost/quality ratio
- [ ] Automated cost budgeting and alert thresholds
- [ ] Integration with cloud billing APIs (AWS, Azure)
- [ ] Per-user cost attribution and team budgeting
- [ ] Cost analysis reports with export to Excel/PDF
