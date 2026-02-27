"""Schema definition and validation for document extraction."""

from typing import Any, Dict

REQUIRED_FIELDS_BY_TYPE = {
    "pay_stub": [
        "employee_name",
        "pay_period",
        "gross_pay",
        "net_pay",
    ],
    "bank_statement": [
        "bank_name",
        "account_number",
        "opening_balance",
        "closing_balance",
    ],
    "investment_statement": [
        "customer_name",
        "investment_year",
        "beginning_value",
        "ending_value",
    ],
    "receipt": [
        "merchant_name",
        "transaction_date",
        "currency",
        "total_amount",
        "tax_amount",
        "receipt_number",
        "payment_method",
        "items",
    ],
}


def validate_and_enforce_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the output follows the required schema with all fields."""
    if not isinstance(data, dict):
        raise ValueError("Output must be a dictionary")

    document_type = data.get("document_type")
    if document_type not in REQUIRED_FIELDS_BY_TYPE:
        allowed = ", ".join(sorted(REQUIRED_FIELDS_BY_TYPE.keys()))
        raise ValueError(f"document_type must be one of: {allowed}")

    # Ensure fields dict exists
    if "fields" not in data:
        data["fields"] = {}
    
    if not isinstance(data["fields"], dict):
        raise ValueError("fields must be a dictionary")
    
    required_fields = REQUIRED_FIELDS_BY_TYPE[document_type]

    # Ensure all required fields are present (use null if missing)
    for field in required_fields:
        if field not in data["fields"]:
            data["fields"][field] = None

    # Remove any extra fields not in the schema
    data["fields"] = {k: data["fields"].get(k) for k in required_fields}
    
    return data
