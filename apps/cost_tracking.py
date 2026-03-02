"""Cost and usage tracking for AI operations."""

import tiktoken
from typing import Dict, Any, Optional


# OpenAI pricing per 1K tokens (March 2026)
PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}

# Token encoder
ENCODER = tiktoken.encoding_for_model("gpt-4")


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text for a given model."""
    try:
        if model not in PRICING:
            model = "gpt-4"
        encoder = tiktoken.encoding_for_model(model)
        return len(encoder.encode(text))
    except Exception:
        # Fallback: ~4 chars per token
        return len(text) // 4


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4"
) -> Dict[str, float]:
    """
    Estimate cost for input/output tokens.
    
    Returns:
        {"input_cost": float, "output_cost": float, "total_cost": float}
    """
    if model not in PRICING:
        model = "gpt-4"
    
    prices = PRICING[model]
    input_cost = (input_tokens / 1000) * prices["input"]
    output_cost = (output_tokens / 1000) * prices["output"]
    total_cost = input_cost + output_cost
    
    return {
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total_cost, 6),
        "model": model
    }


def calculate_hours_saved(
    processing_time_seconds: float,
    manual_review_minutes: int = 30
) -> float:
    """
    Calculate hours saved by automation vs manual processing.
    
    Args:
        processing_time_seconds: Time spent by AI (includes extraction + approval)
        manual_review_minutes: Estimated manual review time (default 30 min)
    
    Returns:
        Hours saved
    """
    manual_time_seconds = manual_review_minutes * 60
    processing_time_min = processing_time_seconds / 60
    
    # Hours saved = manual time - processing time, in hours
    time_saved_minutes = manual_review_minutes - processing_time_min
    time_saved_hours = max(0, time_saved_minutes / 60)
    
    return round(time_saved_hours, 2)


def get_cost_per_approval(
    total_cost: float,
    approvals: int
) -> float:
    """Cost per successful approval."""
    if approvals == 0:
        return 0
    return round(total_cost / approvals, 4)


def get_cost_per_hour_saved(
    total_cost: float,
    total_hours_saved: float
) -> float:
    """Cost to save one hour of human time."""
    if total_hours_saved == 0:
        return 0
    return round(total_cost / total_hours_saved, 2)
