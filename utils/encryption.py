# Copyright (c) 2021 OnePro Cloud Ltd.
#
#   prophet is licensed under Mulan PubL v2.

"""Encryption utilities for sensitive data"""

from cryptography.fernet import Fernet
import base64
import os

_fernet = None


def init_encryption(app):
    """Initialize encryption with key from config"""
    global _fernet
    
    key = app.config.get('ENCRYPTION_KEY')
    if not key:
        # Generate a key if not provided (development only)
        key = Fernet.generate_key()
        app.logger.warning("ENCRYPTION_KEY not set, using generated key (not suitable for production)")
        # Store the generated key in config
        app.config['ENCRYPTION_KEY'] = base64.urlsafe_b64encode(key).decode()
    else:
        # Key is provided - it should be a base64-encoded Fernet key string
        if isinstance(key, str):
            try:
                # Decode the base64-encoded key to get the actual Fernet key
                key = base64.urlsafe_b64decode(key)
            except Exception as e:
                app.logger.error(f"Failed to decode ENCRYPTION_KEY: {e}")
                # If decoding fails, generate a new key (this will break existing encrypted data!)
                app.logger.warning("Generating new encryption key - existing encrypted passwords will be lost!")
                key = Fernet.generate_key()
                app.config['ENCRYPTION_KEY'] = base64.urlsafe_b64encode(key).decode()
        elif isinstance(key, bytes):
            # Key is already bytes, use it directly
            pass
        else:
            app.logger.error(f"Invalid ENCRYPTION_KEY type: {type(key)}")
            key = Fernet.generate_key()
            app.config['ENCRYPTION_KEY'] = base64.urlsafe_b64encode(key).decode()
    
    try:
        _fernet = Fernet(key)
        app.logger.info("Encryption initialized successfully")
    except Exception as e:
        # If key is not valid, generate a new one
        app.logger.error(f"Invalid encryption key, generating new one: {e}")
        key = Fernet.generate_key()
        _fernet = Fernet(key)
        app.config['ENCRYPTION_KEY'] = base64.urlsafe_b64encode(key).decode()
        app.logger.warning("New encryption key generated - existing encrypted passwords will be lost!")


def encrypt_password(password: str) -> str:
    """Encrypt a password"""
    if not _fernet:
        raise RuntimeError("Encryption not initialized")
    if not password:
        return ""
    return _fernet.encrypt(password.encode()).decode()


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt a password"""
    if not _fernet:
        raise RuntimeError("Encryption not initialized")
    if not encrypted_password:
        return ""
    return _fernet.decrypt(encrypted_password.encode()).decode()

