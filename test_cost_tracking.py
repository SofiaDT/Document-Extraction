#!/usr/bin/env python3
"""Test script for cost tracking integration."""

import sys
from pathlib import Path

# Add apps to path
sys.path.insert(0, str(Path(__file__).parent / 'apps'))

from cost_tracking import (
    count_tokens,
    estimate_cost,
    calculate_hours_saved,
    get_cost_per_approval,
    get_cost_per_hour_saved
)
from loan_tracking import get_cost_metrics

def test_token_counting():
    """Test token counting functionality."""
    print("\n📊 Token Counting Test")
    print("=" * 50)
    
    sample_text = "John Doe earned $5,000 in the last period with regular income stability."
    tokens = count_tokens(sample_text, "gpt-4")
    print(f"Sample text: '{sample_text}'")
    print(f"Token count: {tokens}")
    return tokens

def test_cost_estimation():
    """Test cost estimation."""
    print("\n💰 Cost Estimation Test")
    print("=" * 50)
    
    input_tokens = 500
    output_tokens = 200
    
    cost_data = estimate_cost(input_tokens, output_tokens, "gpt-4")
    print(f"Input tokens: {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Model: GPT-4")
    print(f"\nCost breakdown:")
    print(f"  Input cost: ${cost_data['input_cost']:.4f}")
    print(f"  Output cost: ${cost_data['output_cost']:.4f}")
    print(f"  Total cost: ${cost_data['total_cost']:.4f}")
    
    return cost_data['total_cost']

def test_hours_saved():
    """Test hours saved calculation."""
    print("\n⏱️ Hours Saved Test")
    print("=" * 50)
    
    processing_time_seconds = 45
    manual_review_minutes = 30
    
    hours_saved = calculate_hours_saved(processing_time_seconds, manual_review_minutes)
    print(f"Processing time: {processing_time_seconds}s")
    print(f"Manual review time: {manual_review_minutes} minutes")
    print(f"Hours saved: {hours_saved:.2f}h")
    
    return hours_saved

def test_cost_per_metric():
    """Test cost per approval and per hour saved."""
    print("\n📈 Cost Per Metric Test")
    print("=" * 50)
    
    total_cost = 5.50
    approvals = 10
    hours_saved = 2.5
    
    cost_per_approval = get_cost_per_approval(total_cost, approvals)
    cost_per_hour = get_cost_per_hour_saved(total_cost, hours_saved)
    
    print(f"Total cost: ${total_cost:.2f}")
    print(f"Approvals: {approvals}")
    print(f"Hours saved: {hours_saved:.1f}h")
    print(f"\nCost per approval: ${cost_per_approval:.2f}")
    print(f"Cost per hour saved: ${cost_per_hour:.2f}")

def test_aggregated_metrics():
    """Test aggregated cost metrics from loan tracking."""
    print("\n🎯 Aggregated Cost Metrics Test")
    print("=" * 50)
    
    try:
        metrics = get_cost_metrics()
        print(f"Total cost: ${metrics.get('total_cost', 0):.2f}")
        print(f"Total tokens: {metrics.get('total_tokens', 0)}")
        print(f"Total approvals: {metrics.get('approvals', 0)}")
        print(f"Total hours saved: {metrics.get('total_hours_saved', 0):.1f}h")
        print(f"Cost per approval: ${metrics.get('cost_per_approval', 0):.2f}")
        print(f"Cost per hour saved: ${metrics.get('cost_per_hour_saved', 0):.2f}")
        print(f"\nAll metrics loaded successfully!")
    except Exception as e:
        print(f"⚠️ Note: {e}")
        print("This is expected if no applications have been logged yet.")

def main():
    """Run all tests."""
    print("\n🧪 Cost Tracking Integration Tests")
    print("=" * 50)
    
    try:
        test_token_counting()
        test_cost_estimation()
        test_hours_saved()
        test_cost_per_metric()
        test_aggregated_metrics()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\nNext steps:")
        print("1. Run the Loan Checker app to process documents")
        print("2. Approve applications to log cost-tracked records")
        print("3. View Cost & Efficiency Metrics in the Loan Dashboard")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
