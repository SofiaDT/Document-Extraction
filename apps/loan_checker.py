"""Loan Qualification Checker - Assess borrower eligibility using financial documents."""

import json
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import streamlit as st
import yaml
from dotenv import load_dotenv

# Add Document_Extraction to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent / "Document_Extraction"))

from src.config import get_openai_settings
from src.main import extract_document_text
from src.llm_extract import extract_key_values
from loan_tracking import log_application, log_failed_application
from audit_log import log_audit_event, redact_pii
from cost_tracking import count_tokens, estimate_cost

# Load environment
load_dotenv()

st.set_page_config(
    page_title="Loan Qualification Checker",
    layout="wide"
)

# Authentication
with open(Path(__file__).parent / 'config.yaml') as file:
    config = yaml.safe_load(file)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.name = None
    st.session_state.login_time = None

def check_credentials(username, password):
    """Check if credentials are valid"""
    if username in config['credentials']['usernames']:
        stored_password = config['credentials']['usernames'][username]['password']
        if stored_password == password:
            return True, config['credentials']['usernames'][username]['name']
    return False, None


def check_session_timeout(timeout_seconds: int = 1800) -> bool:
    """
    Check if session has timed out (default 30 minutes).
    Returns True if session is still valid, False if expired.
    """
    if not st.session_state.logged_in or not st.session_state.login_time:
        return True  # Not logged in, so timeout check doesn't apply
    
    elapsed = time.time() - st.session_state.login_time
    
    if elapsed > timeout_seconds:
        st.session_state.logged_in = False
        st.session_state.login_time = None
        return False
    
    return True


# Login UI
if not st.session_state.logged_in:
    st.title("Loan Checker Login")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Please log in")
        username = st.text_input("Username", key="username_input")
        password = st.text_input("Password", type="password", key="password_input")
        
        if st.button("Login", use_container_width=True, type="primary"):
            valid, user_name = check_credentials(username, password)
            if valid:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.name = user_name
                st.session_state.login_time = time.time()
                log_audit_event(username, "login", resource="loan_checker")
                st.rerun()
            else:
                log_audit_event(username, "login_failed", resource="loan_checker", status="failure")
                st.error("Invalid username or password")
        
        st.divider()
        st.caption("Demo credentials: admin / admin123 or demo / demo123")
    st.stop()

# Check for session timeout
if not check_session_timeout():
    st.error("Session expired. Please log in again.")
    st.stop()

# Logged in view
with st.sidebar:
    st.write(f"Welcome, **{st.session_state.name}**")
    if st.button("Logout", use_container_width=True):
        log_audit_event(st.session_state.username, "logout", resource="loan_checker")
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.name = None
        st.rerun()

st.title("Loan Qualification Checker")
st.write("Upload your financial documents to assess loan eligibility.")

# Initialize session state
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = {
        "pay_stub": None,
        "bank_statement": None,
        "investment_statement": None
    }

if "extraction_metadata" not in st.session_state:
    st.session_state.extraction_metadata = {
        "pay_stub": {},
        "bank_statement": {},
        "investment_statement": {},
        "processing_start": None,
        "processing_end": None
    }

if "application_logged" not in st.session_state:
    st.session_state.application_logged = False

if "approval_ready" not in st.session_state:
    st.session_state.approval_ready = False

if "approval_data" not in st.session_state:
    st.session_state.approval_data = None

if "show_failure_form" not in st.session_state:
    st.session_state.show_failure_form = False

# Document upload section
st.header("1. Upload Documents")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Pay Stub")
    pay_stub_file = st.file_uploader(
        "Upload pay stub (PDF/PNG/JPG)",
        type=["pdf", "png", "jpg", "jpeg"],
        key="pay_stub"
    )

with col2:
    st.subheader("Bank Statement")
    bank_file = st.file_uploader(
        "Upload bank statement (PDF/PNG/JPG)",
        type=["pdf", "png", "jpg", "jpeg"],
        key="bank_statement"
    )

with col3:
    st.subheader("Investment Statement")
    investment_file = st.file_uploader(
        "Upload investment statement (PDF/PNG/JPG)",
        type=["pdf", "png", "jpg", "jpeg"],
        key="investment_statement"
    )


def extract_from_upload(uploaded_file) -> tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract structured data from uploaded file and capture metadata.
    
    Returns:
        Tuple of (extraction_result, metadata_dict)
    """
    metadata = {
        "file_name": "",
        "file_size_kb": 0,
        "file_type": "",
        "extraction_time_seconds": 0,
        "confidence_score": 0.0,
        "fields_extracted": 0,
        "fields_expected": 0,
        "success": False,
        "error": None
    }
    
    if uploaded_file is None:
        return None, metadata
    
    start_time = time.time()
    
    try:
        # Capture file metadata
        metadata["file_name"] = uploaded_file.name
        metadata["file_size_kb"] = round(uploaded_file.size / 1024, 2)
        metadata["file_type"] = uploaded_file.type or Path(uploaded_file.name).suffix
        
        # Save temporarily
        temp_path = Path(f"temp_{uploaded_file.name}")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract text
        api_key, model = get_openai_settings()
        text = extract_document_text(temp_path)
        
        # Extract structured data
        result = extract_key_values(api_key, model, text, enforce_schema=True)
        
        # Calculate quality metrics
        if result and "fields" in result:
            fields = result["fields"]
            doc_type = result.get("document_type", "")
            
            # Count non-null fields
            metadata["fields_extracted"] = sum(1 for v in fields.values() if v is not None and v != "")
            
            # Expected fields based on doc type
            from src.schema import REQUIRED_FIELDS_BY_TYPE
            if doc_type in REQUIRED_FIELDS_BY_TYPE:
                metadata["fields_expected"] = len(REQUIRED_FIELDS_BY_TYPE[doc_type])
            
            # Calculate confidence score (ratio of extracted to expected)
            if metadata["fields_expected"] > 0:
                metadata["confidence_score"] = metadata["fields_extracted"] / metadata["fields_expected"]
            else:
                metadata["confidence_score"] = 1.0 if metadata["fields_extracted"] > 0 else 0.0
        
        metadata["success"] = True
        
        # Clean up
        temp_path.unlink()
        
        # Record time
        metadata["extraction_time_seconds"] = round(time.time() - start_time, 2)
        
        return result, metadata
        
    except Exception as e:
        metadata["success"] = False
        metadata["error"] = str(e)
        metadata["extraction_time_seconds"] = round(time.time() - start_time, 2)
        st.error(f"Extraction failed: {e}")
        return None, metadata


# Extract button
if st.button("Extract Documents", type="primary"):
    # Reset approval/logging flags for new extraction
    st.session_state.application_logged = False
    st.session_state.approval_ready = False
    st.session_state.approval_data = None
    
    # Start overall timing
    st.session_state.extraction_metadata["processing_start"] = time.time()
    
    with st.spinner("Extracting document data..."):
        if pay_stub_file:
            result, metadata = extract_from_upload(pay_stub_file)
            st.session_state.extracted_data["pay_stub"] = result
            st.session_state.extraction_metadata["pay_stub"] = metadata
        
        if bank_file:
            result, metadata = extract_from_upload(bank_file)
            st.session_state.extracted_data["bank_statement"] = result
            st.session_state.extraction_metadata["bank_statement"] = metadata
        
        if investment_file:
            result, metadata = extract_from_upload(investment_file)
            st.session_state.extracted_data["investment_statement"] = result
            st.session_state.extraction_metadata["investment_statement"] = metadata
    
    # Record end time
    st.session_state.extraction_metadata["processing_end"] = time.time()
    
    st.success("Extraction complete!")
    st.rerun()


# Show extracted data
st.header("2. Extracted Data")

extracted = st.session_state.extracted_data
has_data = any(extracted.values())

if has_data:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if extracted["pay_stub"]:
            st.success("✓ Pay Stub Extracted")
            with st.expander("View Data"):
                st.json(extracted["pay_stub"])
        else:
            st.info("⚠️ Pay Stub Missing")
    
    with col2:
        if extracted["bank_statement"]:
            st.success("✓ Bank Statement Extracted")
            with st.expander("View Data"):
                st.json(extracted["bank_statement"])
        else:
            st.info("⚠️ Bank Statement Missing")
    
    with col3:
        if extracted["investment_statement"]:
            st.success("✓ Investment Statement Extracted")
            with st.expander("View Data"):
                st.json(extracted["investment_statement"])
        else:
            st.info("⚠️ Investment Statement Missing")
else:
    st.info("Upload and extract documents to see data here.")

# Show extraction quality metrics
if has_data and st.session_state.extraction_metadata.get("processing_start"):
    with st.expander("📊 Extraction Quality Metrics", expanded=False):
        metadata = st.session_state.extraction_metadata
        
        # Overall metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if metadata.get("processing_start") and metadata.get("processing_end"):
                total_time = round(metadata["processing_end"] - metadata["processing_start"], 2)
                st.metric("Total Processing Time", f"{total_time}s")
        
        with col2:
            # Average confidence
            confidences = [
                metadata.get("pay_stub", {}).get("confidence_score", 0),
                metadata.get("bank_statement", {}).get("confidence_score", 0),
                metadata.get("investment_statement", {}).get("confidence_score", 0)
            ]
            avg_confidence = sum(confidences) / len([c for c in confidences if c > 0]) if any(confidences) else 0
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        
        with col3:
            # Total fields extracted
            total_fields = sum([
                metadata.get("pay_stub", {}).get("fields_extracted", 0),
                metadata.get("bank_statement", {}).get("fields_extracted", 0),
                metadata.get("investment_statement", {}).get("fields_extracted", 0)
            ])
            st.metric("Total Fields Extracted", total_fields)
        
        # Per-document details
        st.subheader("Per-Document Details")
        
        quality_data = []
        for doc_name, doc_type in [("Pay Stub", "pay_stub"), ("Bank Statement", "bank_statement"), ("Investment", "investment_statement")]:
            doc_meta = metadata.get(doc_type, {})
            if doc_meta.get("success"):
                quality_data.append({
                    "Document": doc_name,
                    "File Name": doc_meta.get("file_name", "N/A"),
                    "Size (KB)": doc_meta.get("file_size_kb", 0),
                    "Time (s)": doc_meta.get("extraction_time_seconds", 0),
                    "Fields": f"{doc_meta.get('fields_extracted', 0)}/{doc_meta.get('fields_expected', 0)}",
                    "Confidence": f"{doc_meta.get('confidence_score', 0):.1%}"
                })
        
        if quality_data:
            import pandas as pd
            st.dataframe(pd.DataFrame(quality_data), use_container_width=True, hide_index=True)


# Loan parameters
st.header("3. Loan Parameters")
col1, col2 = st.columns(2)

with col1:
    proposed_loan_amount = st.number_input(
        "Proposed Loan Amount ($)",
        min_value=0.0,
        value=250000.0,
        step=1000.0
    )

with col2:
    loan_term_years = st.number_input(
        "Loan Term (years)",
        min_value=1,
        max_value=30,
        value=25
    )

interest_rate = st.slider(
    "Interest Rate (%)",
    min_value=0.0,
    max_value=15.0,
    value=6.5,
    step=0.1
)


def calculate_monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    """Calculate monthly loan payment using standard amortization formula."""
    if annual_rate == 0:
        return principal / (years * 12)
    
    monthly_rate = annual_rate / 100 / 12
    num_payments = years * 12
    
    payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
              ((1 + monthly_rate) ** num_payments - 1)
    return payment


monthly_payment = calculate_monthly_payment(proposed_loan_amount, interest_rate, loan_term_years)
st.info(f"**Monthly Payment:** ${monthly_payment:,.2f}")


# Calculate metrics
st.header("4. Qualification Metrics")

if not all(extracted.values()):
    st.warning("⚠️ Please upload and extract all three documents to calculate metrics.")
else:
    try:
        # Extract fields
        pay_stub = extracted["pay_stub"]["fields"]
        bank_stmt = extracted["bank_statement"]["fields"]
        investment = extracted["investment_statement"]["fields"]
        
        net_monthly_income = float(pay_stub.get("net_pay", 0))
        gross_pay = float(pay_stub.get("gross_pay", 0))
        
        opening_balance = float(bank_stmt.get("opening_balance", 0))
        closing_balance = float(bank_stmt.get("closing_balance", 0))
        monthly_expenses = opening_balance - closing_balance
        
        ending_value = float(investment.get("ending_value", 0))
        liquid_assets = closing_balance + ending_value
        
        # Calculate metrics
        st.subheader("Calculated Metrics")
        
        # 1. Payment-to-Income Ratio
        payment_to_income_ratio = monthly_payment / net_monthly_income if net_monthly_income > 0 else 0
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("1. Payment-to-Income Ratio", f"{payment_to_income_ratio:.2%}")
            st.caption("Monthly Payment / Net Monthly Income")
            st.code(f"${monthly_payment:,.2f} / ${net_monthly_income:,.2f} = {payment_to_income_ratio:.2%}")
        with col2:
            if payment_to_income_ratio <= 0.28:
                st.success("✓ Excellent")
            elif payment_to_income_ratio <= 0.36:
                st.warning("⚠️ Acceptable")
            else:
                st.error("✗ Too High")
        
        st.write("---")
        
        # 2. Disposable Income
        disposable_income = net_monthly_income - (monthly_expenses + monthly_payment)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("2. Disposable Income", f"${disposable_income:,.2f}")
            st.caption("Income - (Expenses + Monthly Payment)")
            st.code(f"${net_monthly_income:,.2f} - (${monthly_expenses:,.2f} + ${monthly_payment:,.2f}) = ${disposable_income:,.2f}")
        with col2:
            if disposable_income >= 1000:
                st.success("✓ Strong")
            elif disposable_income >= 0:
                st.warning("⚠️ Tight")
            else:
                st.error("✗ Negative")
        
        st.write("---")
        
        # 3. Liquidity vs Monthly Payment
        liquidity_ratio = liquid_assets / monthly_payment if monthly_payment > 0 else 0
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("3. Liquidity vs Monthly Payment", f"{liquidity_ratio:.1f} months")
            st.caption("Liquid Assets / Monthly Payment")
            st.code(f"(${closing_balance:,.2f} + ${ending_value:,.2f}) / ${monthly_payment:,.2f} = {liquidity_ratio:.1f} months")
        with col2:
            if liquidity_ratio >= 6:
                st.success("✓ Strong")
            elif liquidity_ratio >= 3:
                st.warning("⚠️ Moderate")
            else:
                st.error("✗ Weak")
        
        st.write("---")
        
        # Overall assessment
        st.header("4. Overall Assessment")
        
        # Count strong signals
        strong_signals = sum([
            payment_to_income_ratio <= 0.28,
            disposable_income >= 1000,
            liquidity_ratio >= 6
        ])
        
        # Determine qualification
        if strong_signals >= 3:
            qualification = "Likely to Qualify"
            st.success("✅ **LIKELY TO QUALIFY** - Strong financial profile")
        elif strong_signals >= 2:
            qualification = "Conditional Approval"
            st.warning("⚠️ **CONDITIONAL APPROVAL** - Good profile with minor concerns")
        else:
            qualification = "High Risk"
            st.error("❌ **HIGH RISK** - Weak financial indicators")
        
        # Summary table
        st.subheader("Summary")
        summary_data = {
            "Metric": [
                "Payment-to-Income Ratio",
                "Disposable Income",
                "Liquidity vs Payment"
            ],
            "Value": [
                f"{payment_to_income_ratio:.2%}",
                f"${disposable_income:,.2f}",
                f"{liquidity_ratio:.1f} months"
            ],
            "Target": ["≤ 28%", "≥ $1,000", "≥ 6 months"],
            "Status": [
                "✓" if payment_to_income_ratio <= 0.28 else "✗",
                "✓" if disposable_income >= 1000 else "✗",
                "✓" if liquidity_ratio >= 6 else "✗"
            ]
        }
        st.table(summary_data)
        
        # Prepare application data for approval
        applicant_name = pay_stub.get("employee_name", "Unknown")
        
        # Get metadata for each document
        metadata = st.session_state.extraction_metadata
        
        # Calculate total processing time
        if metadata.get("processing_start") and metadata.get("processing_end"):
            total_processing_time = round(metadata["processing_end"] - metadata["processing_start"], 2)
        else:
            total_processing_time = sum([
                metadata.get("pay_stub", {}).get("extraction_time_seconds", 0),
                metadata.get("bank_statement", {}).get("extraction_time_seconds", 0),
                metadata.get("investment_statement", {}).get("extraction_time_seconds", 0)
            ])
        
        # Get real confidence scores
        confidence_scores = {
            "pay_stub": metadata.get("pay_stub", {}).get("confidence_score", 0.0),
            "bank_statement": metadata.get("bank_statement", {}).get("confidence_score", 0.0),
            "investment_statement": metadata.get("investment_statement", {}).get("confidence_score", 0.0)
        }
        
        # Build quality notes
        quality_notes = []
        for doc_type in ["pay_stub", "bank_statement", "investment_statement"]:
            doc_meta = metadata.get(doc_type, {})
            if doc_meta.get("success"):
                quality_notes.append(
                    f"{doc_type}: {doc_meta.get('fields_extracted', 0)}/{doc_meta.get('fields_expected', 0)} fields"
                )
        
        notes = f"Monthly payment: ${monthly_payment:,.2f} | " + " | ".join(quality_notes)
        
        # Store approval data in session
        st.session_state.approval_data = {
            "applicant_name": applicant_name,
            "username": st.session_state.username,
            "documents": {
                "pay_stub": metadata.get("pay_stub", {}).get("file_name", "N/A"),
                "bank_statement": metadata.get("bank_statement", {}).get("file_name", "N/A"),
                "investment_statement": metadata.get("investment_statement", {}).get("file_name", "N/A")
            },
            "metrics": {
                "payment_to_income_ratio": payment_to_income_ratio,
                "disposable_income": disposable_income,
                "liquidity_vs_payment": liquidity_ratio
            },
            "qualification": qualification,
            "extraction_confidence": confidence_scores,
            "processing_time": total_processing_time,
            "notes": notes
        }
        
        st.session_state.approval_ready = True
        
        st.divider()
        
        # Approval button section
        st.header("5. Review & Approve")
        st.info("Review the metrics above. Click Approve to save this application to the dashboard, or upload new documents to start over.")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("Approve & Log", type="primary", use_container_width=True):
                try:
                    data = st.session_state.approval_data
                    
                    # Redact PII from notes for audit trail
                    redacted_applicant = redact_pii(data["applicant_name"])
                    redacted_notes = data["notes"].replace(data["applicant_name"], redacted_applicant)
                    
                    # Calculate token usage and cost
                    # Count tokens for all extracted text and document data
                    total_input_tokens = 0
                    total_output_tokens = 0
                    
                    for doc_type in ["pay_stub", "bank_statement", "investment_statement"]:
                        doc_meta = metadata.get(doc_type, {})
                        if doc_meta.get("success"):
                            # Estimate input tokens from document content
                            total_input_tokens += count_tokens(redacted_notes, "gpt-4")
                    
                    # Estimate output tokens from extracted data (roughly 50-100 tokens per doc)
                    total_output_tokens = 300  # Conservative estimate for 3 documents + metrics
                    
                    # Calculate cost
                    cost_data = estimate_cost(total_input_tokens, total_output_tokens, "gpt-4")
                    total_cost = cost_data["total_cost"]
                    
                    app_id = log_application(
                        applicant_name=data["applicant_name"],
                        username=data["username"],
                        documents=data["documents"],
                        metrics=data["metrics"],
                        qualification=data["qualification"],
                        extraction_confidence=data["extraction_confidence"],
                        processing_time=data["processing_time"],
                        notes=redacted_notes,
                        input_tokens=total_input_tokens,
                        output_tokens=total_output_tokens,
                        cost_usd=total_cost
                    )
                    
                    # Log audit event
                    log_audit_event(
                        st.session_state.username,
                        "approved_application",
                        resource=app_id,
                        details={
                            "qualification": data["qualification"],
                            "applicant_partial": redacted_applicant
                        }
                    )
                    
                    st.session_state.application_logged = True
                    st.success(f"Application logged: {app_id}")
                    st.info(f"View in Loan Dashboard | Processing time: {data['processing_time']:.1f}s")
                    
                except Exception as log_error:
                    st.error(f"Error logging application: {log_error}")
        
        with col2:
            if st.button("Start Over", use_container_width=True):
                st.session_state.show_failure_form = True
        
        # Failure reason dialog
        if st.session_state.get("show_failure_form", False):
            st.divider()
            st.warning("Why are you starting over? Please select the reason below so we can track failed applications.")
            
            failure_reason = st.radio(
                "Reason for not approving:",
                options=["missing_data", "invalid_data", "insufficient_funds", "document_quality", "other"],
                format_func=lambda x: {
                    "missing_data": "Missing data or documents",
                    "invalid_data": "Invalid or inconsistent data",
                    "insufficient_funds": "Insufficient income/funds",
                    "document_quality": "Poor document quality",
                    "other": "Other reason"
                }.get(x, x),
                key="failure_reason_select"
            )
            
            additional_notes = st.text_area(
                "Additional notes (optional):",
                placeholder="Describe what went wrong...",
                key="failure_notes"
            )
            
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                if st.button("Log Failure & Start Over", type="secondary", use_container_width=True):
                    try:
                        data = st.session_state.approval_data
                        
                        # Log the failed application
                        failed_app_id = log_failed_application(
                            applicant_name=data.get("applicant_name", "Unknown"),
                            username=st.session_state.username,
                            failure_reason=failure_reason,
                            documents=data.get("documents", {}),
                            extraction_confidence=data.get("extraction_confidence", {}),
                            processing_time=data.get("processing_time", 0),
                            notes=additional_notes if additional_notes else None
                        )
                        
                        # Log audit event
                        redacted_applicant = redact_pii(data.get("applicant_name", "Unknown"))
                        log_audit_event(
                            st.session_state.username,
                            "failed_application",
                            resource=failed_app_id,
                            details={
                                "failure_reason": failure_reason,
                                "applicant_partial": redacted_applicant
                            }
                        )
                        
                        # Clear form and reset
                        st.session_state.extracted_data = {
                            "pay_stub": None,
                            "bank_statement": None,
                            "investment_statement": None
                        }
                        st.session_state.approval_ready = False
                        st.session_state.approval_data = None
                        st.session_state.show_failure_form = False
                        
                        st.success(f"✓ Failed application logged: {failed_app_id}")
                        st.info("Ready to process new applications.")
                        time.sleep(2)
                        st.rerun()
                    except Exception as fail_error:
                        st.error(f"Error logging failed application: {fail_error}")
            
            with col_cancel:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_failure_form = False
                    st.rerun()
        
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        st.write("Please ensure all documents are properly extracted with valid numeric fields.")
