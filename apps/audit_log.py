"""Audit logging for security and compliance tracking."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


AUDIT_DIR = Path(__file__).parent.parent / "data/output"
AUDIT_LOG_FILE = AUDIT_DIR / "audit_log.json"


def ensure_audit_dir():
    """Ensure audit directory exists."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def log_audit_event(
    username: str,
    action: str,
    resource: str = "",
    status: str = "success",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an audit event for compliance and security tracking.
    
    Args:
        username: User performing the action
        action: Action type (login, logout, approved_application, viewed_dashboard, etc.)
        resource: Resource affected (e.g., application ID, file name)
        status: success/failure
        details: Additional context (without sensitive data)
    """
    ensure_audit_dir()
    
    # Load existing events
    events = []
    if AUDIT_LOG_FILE.exists():
        try:
            with open(AUDIT_LOG_FILE, 'r') as f:
                events = json.load(f)
        except Exception:
            events = []
    
    # Create event (never log sensitive data)
    event = {
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "action": action,
        "resource": resource,
        "status": status,
    }
    
    if details:
        event["details"] = details
    
    events.append(event)
    
    # Save updated log
    try:
        with open(AUDIT_LOG_FILE, 'w') as f:
            json.dump(events, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not write audit log: {e}")


def redact_pii(text: str, keep_chars: int = 3) -> str:
    """
    Redact personally identifiable information.
    Keep only last N characters for audit trails.
    
    Example: "MICHAEL D BRYAN" -> "***RYAN"
    """
    if not text or len(text) <= keep_chars:
        return "***"
    return "***" + text[-keep_chars:]


def get_audit_log(
    username: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100
) -> list:
    """
    Retrieve audit log entries with optional filtering.
    
    Args:
        username: Filter by username
        action: Filter by action type
        limit: Max number of events to return
    """
    ensure_audit_dir()
    
    if not AUDIT_LOG_FILE.exists():
        return []
    
    try:
        with open(AUDIT_LOG_FILE, 'r') as f:
            events = json.load(f)
    except Exception:
        return []
    
    # Filter
    if username:
        events = [e for e in events if e.get('username') == username]
    if action:
        events = [e for e in events if e.get('action') == action]
    
    # Return most recent, limited
    return sorted(events, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]


def get_user_activity_summary(username: str) -> Dict[str, Any]:
    """Get summary statistics for a user."""
    events = get_audit_log(username=username, limit=1000)
    
    if not events:
        return {"total_events": 0}
    
    action_counts = {}
    first_activity = None
    last_activity = None
    
    for event in reversed(events):  # Reversed because events are already sorted descending
        action = event.get('action', 'unknown')
        action_counts[action] = action_counts.get(action, 0) + 1
        
        if first_activity is None:
            first_activity = event.get('timestamp')
        last_activity = event.get('timestamp')
    
    return {
        "total_events": len(events),
        "action_breakdown": action_counts,
        "first_activity": first_activity,
        "last_activity": last_activity
    }
