#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate encryption key for Prophet Web application

Usage:
    python tools/generate_encryption_key.py

This script generates a Fernet encryption key that can be used as ENCRYPTION_KEY
environment variable to ensure consistent encryption/decryption across service restarts.
"""

from cryptography.fernet import Fernet
import base64

def generate_key():
    """Generate a new Fernet encryption key"""
    key = Fernet.generate_key()
    encoded_key = base64.urlsafe_b64encode(key).decode()
    return encoded_key

if __name__ == '__main__':
    key = generate_key()
    print("=" * 60)
    print("ENCRYPTION_KEY for Prophet Web Application")
    print("=" * 60)
    print()
    print("Generated key (copy this value):")
    print(key)
    print()
    print("=" * 60)
    print("How to use:")
    print("=" * 60)
    print()
    print("1. Set as environment variable (Linux/macOS):")
    print(f"   export ENCRYPTION_KEY='{key}'")
    print()
    print("2. Set as environment variable (Windows CMD):")
    print(f"   set ENCRYPTION_KEY={key}")
    print()
    print("3. Set as environment variable (Windows PowerShell):")
    print(f"   $env:ENCRYPTION_KEY='{key}'")
    print()
    print("4. Add to .env file (create if not exists):")
    print(f"   ENCRYPTION_KEY={key}")
    print()
    print("5. For systemd service, add to /etc/systemd/system/prophet.service:")
    print("   [Service]")
    print(f"   Environment='ENCRYPTION_KEY={key}'")
    print()
    print("=" * 60)
    print("IMPORTANT:")
    print("=" * 60)
    print("- Keep this key secure and do not share it publicly")
    print("- Use the same key across all service restarts to decrypt existing passwords")
    print("- If you change the key, all encrypted passwords in the database will be lost")
    print("- In production, use a secure key management system")
    print("=" * 60)

