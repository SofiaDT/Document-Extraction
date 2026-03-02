"""Encryption utilities for sensitive data at rest."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
from cryptography.fernet import Fernet, InvalidToken


# Encryption key file location
ENCRYPTION_KEY_FILE = Path(__file__).parent.parent / "data/output" / ".encryption_key"


def ensure_encryption_key() -> str:
    """
    Ensure encryption key exists. Creates one if it doesn't.
    
    IMPORTANT: Store this key securely in production (e.g., AWS Secrets Manager, HashiCorp Vault)
    Never commit .encryption_key to version control.
    """
    ENCRYPTION_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    if ENCRYPTION_KEY_FILE.exists():
        with open(ENCRYPTION_KEY_FILE, 'rb') as f:
            return f.read()
    
    # Generate new key
    key = Fernet.generate_key()
    with open(ENCRYPTION_KEY_FILE, 'wb') as f:
        f.write(key)
    
    # Restrict permissions (Unix-like systems)
    try:
        os.chmod(ENCRYPTION_KEY_FILE, 0o600)  # Read/write for owner only
    except Exception:
        pass  # Windows may not support this
    
    return key


def encrypt_data(data: Dict[str, Any]) -> bytes:
    """
    Encrypt a dictionary to bytes.
    """
    key = ensure_encryption_key()
    cipher = Fernet(key)
    
    # Serialize to JSON
    json_str = json.dumps(data, indent=2)
    
    # Encrypt
    encrypted = cipher.encrypt(json_str.encode())
    return encrypted


def decrypt_data(encrypted_bytes: bytes) -> Dict[str, Any]:
    """
    Decrypt bytes back to a dictionary.
    """
    try:
        key = ensure_encryption_key()
        cipher = Fernet(key)
        
        # Decrypt
        decrypted = cipher.decrypt(encrypted_bytes)
        
        # Deserialize from JSON
        return json.loads(decrypted.decode())
    except InvalidToken:
        raise ValueError("Decryption failed - invalid key or corrupted data")
    except Exception as e:
        raise ValueError(f"Decryption error: {e}")


def encrypt_file(file_path: Path) -> None:
    """
    Encrypt a JSON file in place.
    Creates a backup before encrypting.
    """
    if not file_path.exists():
        return
    
    # Read current data
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Create backup
    backup_path = file_path.with_stem(file_path.stem + "_backup")
    with open(backup_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Encrypt and write
    encrypted = encrypt_data(data)
    with open(file_path, 'wb') as f:
        f.write(encrypted)
    
    print(f"✓ Encrypted {file_path}")
    print(f"  Backup saved to {backup_path}")


def decrypt_file(file_path: Path) -> Dict[str, Any]:
    """
    Decrypt a JSON file that was encrypted.
    """
    with open(file_path, 'rb') as f:
        encrypted_bytes = f.read()
    
    return decrypt_data(encrypted_bytes)


def is_encrypted_file(file_path: Path) -> bool:
    """
    Check if a file appears to be encrypted (cannot be parsed as JSON).
    """
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        return False  # Successfully parsed as JSON, not encrypted
    except (json.JSONDecodeError, UnicodeDecodeError):
        return True  # Not JSON, likely encrypted
