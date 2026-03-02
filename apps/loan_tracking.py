"""Loan application tracking utilities for analytics and dashboard."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


OUTPUT_DIR = Path(__file__).parent.parent / "data/output"
APPLICATIONS_FILE = OUTPUT_DIR / "loan_applications.json"


def ensure_tracking_dir():
    """Ensure output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_applications() -> List[Dict[str, Any]]:
    """Load all tracked loan applications."""
    ensure_tracking_dir()
    if not APPLICATIONS_FILE.exists():
        return []
    
    try:
        with open(APPLICATIONS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []


def save_applications(applications: List[Dict[str, Any]]):
    """Save applications to tracking file."""
    ensure_tracking_dir()
    with open(APPLICATIONS_FILE, 'w') as f:
        json.dump(applications, f, indent=2)


def log_application(
    applicant_name: str,
    username: str,
    documents: Dict[str, str],
    metrics: Dict[str, float],
    qualification: str,
    extraction_confidence: Dict[str, float],
    processing_time: float,
    notes: Optional[str] = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0
) -> str:
    """
    Log a loan application review with cost tracking.
    
    Returns:
        Application ID
    """
    applications = load_applications()
    
    app_id = f"APP-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(applications) + 1}"
    
    application = {
        "application_id": app_id,
        "timestamp": datetime.now().isoformat(),
        "applicant_name": applicant_name,
        "reviewed_by": username,
        "documents": documents,
        "metrics": metrics,
        "qualification": qualification,
        "extraction_confidence": extraction_confidence,
        "processing_time_seconds": processing_time,
        "notes": notes,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 6)
    }
    
    applications.append(application)
    save_applications(applications)
    
    return app_id


def log_failed_application(
    applicant_name: str,
    username: str,
    failure_reason: str,
    documents: Optional[Dict[str, str]] = None,
    extraction_confidence: Optional[Dict[str, float]] = None,
    processing_time: float = 0.0,
    notes: Optional[str] = None
) -> str:
    """
    Log a failed application review.
    
    Args:
        applicant_name: Name of the applicant
        username: User who reviewed the application
        failure_reason: Reason for failure (e.g., "missing_data", "other")
        documents: Extracted document paths (if any)
        extraction_confidence: Confidence scores (if any)
        processing_time: Time spent before failure
        notes: Additional notes about the failure
    
    Returns:
        Application ID
    """
    applications = load_applications()
    
    app_id = f"APP-{datetime.now().strftime('%Y%m%d-%H%M%S')}-FAILED-{len(applications) + 1}"
    
    application = {
        "application_id": app_id,
        "timestamp": datetime.now().isoformat(),
        "applicant_name": applicant_name,
        "reviewed_by": username,
        "status": "failed",
        "failure_reason": failure_reason,
        "documents": documents or {},
        "extraction_confidence": extraction_confidence or {},
        "processing_time_seconds": processing_time,
        "notes": notes
    }
    
    applications.append(application)
    save_applications(applications)
    
    return app_id


def get_applications_by_date_range(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Filter applications by date range."""
    applications = load_applications()
    
    if not start_date and not end_date:
        return applications
    
    filtered = []
    for app in applications:
        app_date = app.get("timestamp", "")
        if start_date and app_date < start_date:
            continue
        if end_date and app_date > end_date:
            continue
        filtered.append(app)
    
    return filtered


def get_applications_by_user(username: str) -> List[Dict[str, Any]]:
    """Get all applications reviewed by a specific user."""
    applications = load_applications()
    return [app for app in applications if app.get("reviewed_by") == username]


def get_qualification_stats() -> Dict[str, int]:
    """Get count of applications by qualification level."""
    applications = load_applications()
    stats = {"Likely to Qualify": 0, "Conditional Approval": 0, "High Risk": 0}
    
    for app in applications:
        qual = app.get("qualification", "")
        if qual in stats:
            stats[qual] += 1
    
    return stats


def get_average_processing_time() -> float:
    """Get average processing time across all applications."""
    applications = load_applications()
    if not applications:
        return 0.0
    
    times = [app.get("processing_time_seconds", 0) for app in applications]
    return sum(times) / len(times) if times else 0.0


def get_document_confidence_stats() -> Dict[str, Dict[str, float]]:
    """Get average confidence scores by document type."""
    applications = load_applications()
    
    doc_stats = {
        "pay_stub": [],
        "bank_statement": [],
        "investment_statement": []
    }
    
    for app in applications:
        conf = app.get("extraction_confidence", {})
        for doc_type in doc_stats:
            if doc_type in conf:
                doc_stats[doc_type].append(conf[doc_type])
    
    # Calculate averages and add stats
    result = {}
    for doc_type, values in doc_stats.items():
        if values:
            result[doc_type] = {
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values)
            }
        else:
            result[doc_type] = {
                "average": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0
            }
    
    return result


def get_quality_issues() -> List[Dict[str, Any]]:
    """Identify applications with quality issues (low confidence, long processing)."""
    applications = load_applications()
    issues = []
    
    for app in applications:
        app_issues = []
        
        # Check confidence scores
        conf = app.get("extraction_confidence", {})
        for doc_type, score in conf.items():
            if score < 0.7:
                app_issues.append(f"Low confidence in {doc_type}: {score:.1%}")
        
        # Check processing time (flag if > 30 seconds)
        proc_time = app.get("processing_time_seconds", 0)
        if proc_time > 30:
            app_issues.append(f"Slow processing: {proc_time:.1f}s")
        
        # Check for missing metrics
        metrics = app.get("metrics", {})
        if not all(k in metrics for k in ["payment_to_income_ratio", "disposable_income", "liquidity_vs_payment"]):
            app_issues.append("Missing financial metrics")
        
        if app_issues:
            issues.append({
                "application_id": app.get("application_id"),
                "applicant_name": app.get("applicant_name"),
                "timestamp": app.get("timestamp"),
                "issues": app_issues
            })
    
    return issues


def get_total_cost() -> float:
    """Get total spend across all applications."""
    applications = load_applications()
    return sum(app.get("cost_usd", 0) for app in applications)


def get_monthly_cost(year: int, month: int) -> float:
    """Get spend for a specific month."""
    applications = load_applications()
    monthly_cost = 0
    for app in applications:
        try:
            ts = datetime.fromisoformat(app.get("timestamp", ""))
            if ts.year == year and ts.month == month:
                monthly_cost += app.get("cost_usd", 0)
        except Exception:
            pass
    return round(monthly_cost, 2)


def get_cost_metrics() -> Dict[str, float]:
    """Get cost aggregations and per-unit metrics."""
    applications = load_applications()
    
    if not applications:
        return {
            "total_cost": 0.0,
            "total_tokens": 0,
            "avg_cost_per_app": 0.0,
            "approvals": 0,
            "cost_per_approval": 0.0,
            "total_hours_saved": 0.0,
        }
    
    total_cost = sum(app.get("cost_usd", 0) for app in applications)
    total_input_tokens = sum(app.get("input_tokens", 0) for app in applications)
    total_output_tokens = sum(app.get("output_tokens", 0) for app in applications)
    total_tokens = total_input_tokens + total_output_tokens
    
    # Count approvals (Likely to Qualify or Conditional)
    approvals = sum(1 for app in applications if app.get("qualification") in 
                   ["Likely to Qualify", "Conditional Approval"])
    
    # Calculate hours saved (15 min baseline per app)
    total_hours_saved = sum(
        max(0, (15 - (app.get("processing_time_seconds", 0) / 60)) / 60)
        for app in applications
    )
    
    return {
        "total_cost": round(total_cost, 2),
        "total_tokens": total_tokens,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "avg_cost_per_app": round(total_cost / len(applications), 4) if applications else 0,
        "approvals": approvals,
        "cost_per_approval": round(total_cost / approvals, 4) if approvals > 0 else 0,
        "total_hours_saved": round(total_hours_saved, 1),
    }

