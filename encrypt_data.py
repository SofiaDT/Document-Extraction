#!/usr/bin/env python3
"""
Security utility script for encrypting sensitive loan data.

Usage:
    python encrypt_data.py  # Encrypt loan_applications.json
"""

import json
from pathlib import Path
from apps.encryption import encrypt_file, decrypt_file, is_encrypted_file

def main():
    output_dir = Path("data/output")
    loan_file = output_dir / "loan_applications.json"
    backup_file = output_dir / "loan_applications_backup.json"
    
    print("=" * 60)
    print("LOAN DATA ENCRYPTION UTILITY")
    print("=" * 60)
    
    if not loan_file.exists():
        print(f"❌ File not found: {loan_file}")
        return
    
    # Check if already encrypted
    if is_encrypted_file(loan_file):
        print(f"✓ {loan_file} is already encrypted")
        
        # Offer to decrypt for verification
        decrypt_choice = input("\nDecrypt for verification? (y/n): ").strip().lower()
        if decrypt_choice == 'y':
            try:
                print("\n🔓 Decrypting...")
                data = decrypt_file(loan_file)
                print(f"✓ Successfully decrypted {len(data)} applications")
                print("\nSample application:")
                if data:
                    for key, value in list(data[0].items())[:3]:
                        print(f"  {key}: {value}")
            except Exception as e:
                print(f"❌ Decryption failed: {e}")
        return
    
    # Show current file size
    file_size = loan_file.stat().st_size
    print(f"\n📄 File: {loan_file}")
    print(f"📊 Current size: {file_size:,} bytes")
    
    # Show sample data
    try:
        with open(loan_file, 'r') as f:
            data = json.load(f)
        print(f"📈 Applications: {len(data)}")
        if data:
            print(f"   Last modified: {data[-1].get('timestamp', 'N/A')}")
    except Exception as e:
        print(f"⚠️  Could not read file: {e}")
        return
    
    # Confirm encryption
    print("\n" + "=" * 60)
    print("ENCRYPTION ACTION")
    print("=" * 60)
    print("This will:")
    print("  1. Create a backup: loan_applications_backup.json")
    print("  2. Encrypt the original file with AES-256")
    print("  3. Generate encryption key in: data/output/.encryption_key")
    print("\n⚠️  IMPORTANT:")
    print("  - Add .encryption_key to your secrets manager in production")
    print("  - Without the key, encrypted data is unrecoverable")
    print("  - Keep .gitignore updated to prevent committing sensitive files")
    print("\n" + "=" * 60)
    
    choice = input("\nProceed with encryption? (yes/no): ").strip().lower()
    
    if choice != 'yes':
        print("❌ Encryption cancelled")
        return
    
    # Perform encryption
    try:
        print("\n🔒 Encrypting...")
        encrypt_file(loan_file)
        print("✓ Encryption complete!")
        
        # Verify
        if is_encrypted_file(loan_file):
            encrypted_size = loan_file.stat().st_size
            print(f"\n✓ File is now encrypted")
            print(f"✓ New size: {encrypted_size:,} bytes")
            print(f"✓ Backup: {backup_file}")
            print(f"✓ Key: data/output/.encryption_key")
        
    except Exception as e:
        print(f"❌ Encryption failed: {e}")


if __name__ == "__main__":
    main()
