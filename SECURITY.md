# Security Implementation Guide

## What Was Added

### 1. Session Timeout
- **Location**: `apps/loan_checker.py`
- **Feature**: Auto-logout after 30 minutes of inactivity
- **Customizable**: Change timeout in `check_session_timeout(timeout_seconds=1800)`

### 2. Audit Logging
- **Location**: `apps/audit_log.py`
- **Scope**: Tracks all user actions (login, logout, approvals, etc.)
- **Storage**: `data/output/audit_log.json` (add to .gitignore)
- **Format**: JSON with timestamp, username, action, resource, status, details

**Logged Events:**
```
- login              : User logged in
- login_failed       : Failed login attempt
- logout             : User logged out
- approved_application : Application approved and saved
```

### 3. PII Redaction
- **Location**: `apps/audit_log.py` - `redact_pii()` function
- **Default**: Keeps only last 3 characters of names
- **Example**: "MICHAEL D BRYAN" → "***BRYAN"
- **Usage**: Applied to all applicant names in logs

### 4. Encryption-at-Rest (Optional)
- **Location**: `apps/encryption.py`
- **Algorithm**: Fernet (256-bit AES)
- **Key Storage**: `data/output/.encryption_key`
- **Utility Script**: `encrypt_data.py` for manual encryption

## How to Use

### Access Audit Logs
```bash
# View recent audit events
cat data/output/audit_log.json | python3 -m json.tool | tail -20

# Or programmatically
python3 -c "
from apps.audit_log import get_audit_log, get_user_activity_summary
events = get_audit_log(username='admin', limit=10)
for e in events:
    print(f\"{e['timestamp']} | {e['action']} | {e['resource']}\")
"
```

### Encrypt Loan Data
```bash
# Interactive encryption with prompts
python3 encrypt_data.py

# Or programmatically
from apps.encryption import encrypt_file
from pathlib import Path
encrypt_file(Path("data/output/loan_applications.json"))
```

### Monitor User Activity
```bash
# Get summary for a user
python3 -c "
from apps.audit_log import get_user_activity_summary
summary = get_user_activity_summary('admin')
print(f\"Admin has {summary['total_events']} audit events\")
print(f\"Actions: {summary['action_breakdown']}\")
"
```

## Security Checklist

- [x] **Session Timeout** - Users auto-logout after 30 min inactivity
- [x] **Audit Logging** - All actions tracked with timestamp and user
- [x] **PII Redaction** - Names redacted in logs (last 3 chars only)
- [x] **Login Tracking** - Failed attempts logged
- [x] **Approval Logging** - All approvals recorded with app ID
- [ ] **Encryption-at-Rest** - Manual step: run `python3 encrypt_data.py`
- [ ] **Role-Based Access** - Future: admin/officer/auditor roles
- [ ] **Key Management** - Future: Move .encryption_key to secrets manager

## Configuration

### Session Timeout
Edit `apps/loan_checker.py` line ~60:
```python
def check_session_timeout(timeout_seconds: int = 1800):  # 30 minutes
```

### PII Redaction Length
Edit `apps/audit_log.py` line ~77:
```python
def redact_pii(text: str, keep_chars: int = 3):  # Keep last 3 chars
```

### Encryption Key Path
Edit `apps/encryption.py` line ~9:
```python
ENCRYPTION_KEY_FILE = Path(__file__).parent.parent / "data/output" / ".encryption_key"
```

## Production Recommendations

1. **Encryption Key Management**
   - Store in AWS Secrets Manager or HashiCorp Vault
   - Rotate keys annually
   - Never commit .encryption_key to version control

2. **Audit Log Management**
   - Archive logs older than 1 year
   - Store archives in immutable storage (AWS Glacier, etc.)
   - Monitor for suspicious patterns

3. **Access Controls (Next Phase)**
   - Admin: View all data, manage users
   - Loan Officer: Approve/view own applications
   - Auditor: Read-only access to audit logs

4. **Monitoring & Alerts**
   - Alert on failed login attempts (>5 in 10 min)
   - Alert on unusual approval patterns
   - Daily audit log summary emails

## Files Added

- `apps/audit_log.py` - Audit logging utilities
- `apps/encryption.py` - Encryption/decryption utilities
- `encrypt_data.py` - Interactive encryption script
- `SECURITY.md` - This file

## Files Modified

- `apps/loan_checker.py` - Added session timeout, audit logging, PII redaction
- `requirements.txt` - Added cryptography package
- `.gitignore` - Protected encryption key and sensitive files
- `README.md` - Documented security features

