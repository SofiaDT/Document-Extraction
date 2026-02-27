"""Loan Qualification Checker - Assess borrower eligibility using financial documents."""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import streamlit as st
from dotenv import load_dotenv

# Add Document_Extraction to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent / "Document_Extraction"))

from src.config import get_openai_settings
from src.main import extract_document_text
from src.llm_extract import extract_key_values

# Load environment
load_dotenv()

st.set_page_config(
    page_title="Loan Qualification Checker",
    layout="wide"
)

st.title("💰 Loan Qualification Checker")
st.write("Upload your financial documents to assess loan eligibility.")

# Initialize session state
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = {
        "pay_stub": None,
        "bank_statement": None,
        "investment_statement": None
    }

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


def extract_from_upload(uploaded_file) -> Optional[Dict[str, Any]]:
    """Extract structured data from uploaded file."""
    if uploaded_file is None:
        return None
    
    try:
        # Save temporarily
        temp_path = Path(f"temp_{uploaded_file.name}")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract text
        api_key, model = get_openai_settings()
        text = extract_document_text(temp_path)
        
        # Extract structured data
        result = extract_key_values(api_key, model, text, enforce_schema=True)
        
        # Clean up
        temp_path.unlink()
        
        return result
    except Exception as e:
        st.error(f"Extraction failed: {e}")
        return None


# Extract button
if st.button("Extract Documents", type="primary"):
    with st.spinner("Extracting document data..."):
        if pay_stub_file:
            st.session_state.extracted_data["pay_stub"] = extract_from_upload(pay_stub_file)
        if bank_file:
            st.session_state.extracted_data["bank_statement"] = extract_from_upload(bank_file)
        if investment_file:
            st.session_state.extracted_data["investment_statement"] = extract_from_upload(investment_file)
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
        
        if strong_signals >= 3:
            st.success("✅ **LIKELY TO QUALIFY** - Strong financial profile")
        elif strong_signals >= 2:
            st.warning("⚠️ **CONDITIONAL APPROVAL** - Good profile with minor concerns")
        elif strong_signals >= 1:
            st.warning("⚠️ **NEEDS REVIEW** - Mixed signals, manual assessment recommended")
        else:
            st.error("❌ **HIGH RISK** - Multiple weak indicators")
        
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
        
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        st.write("Please ensure all documents are properly extracted with valid numeric fields.")
