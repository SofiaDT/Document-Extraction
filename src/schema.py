"""Schema definition and validation for insurance invoice extraction."""

from typing import Any, Dict

REQUIRED_FIELDS = [
    "insurance_company",
    "insurance_company_home_office",
    "mailing_address",
    "client_name",
    "account_number",
    "attention",
    "invoice_number",
    "client_address",
    "adjustment_type",
    "effective_date_start",
    "effective_date_end",
    "audited_premium",
    "retrospective_premium",
    "previously_billed_premium",
    "gross_adjustment",
    "dividend_on_retro_premium",
    "previously_billed_dividend",
    "dividend_offset",
    "balance_due_company",
]


def validate_and_enforce_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the output follows the required schema with all fields."""
    if not isinstance(data, dict):
        raise ValueError("Output must be a dictionary")
    
    # Ensure document_type is set
    if "document_type" not in data:
        data["document_type"] = "insurance_invoice"
    
    # Ensure fields dict exists
    if "fields" not in data:
        data["fields"] = {}
    
    if not isinstance(data["fields"], dict):
        raise ValueError("fields must be a dictionary")
    
    # Ensure all required fields are present (use null if missing)
    for field in REQUIRED_FIELDS:
        if field not in data["fields"]:
            data["fields"][field] = None
    
    # Remove any extra fields not in the schema
    data["fields"] = {k: v for k, v in data["fields"].items() if k in REQUIRED_FIELDS}
    
    return data
