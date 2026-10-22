#!/usr/bin/env python3
"""
Encryption utilities for .env files in the onde_monitor project.
Provides functions to encrypt and decrypt environment variable files.
"""

from pathlib import Path
import os
import subprocess
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


def generate_encryption_key(password: str, salt: bytes = None) -> bytes:
    """Generate encryption key using PBKDF2"""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def get_keychain_credential(service: str, account: str) -> str:
    """Retrieve a password from macOS Keychain."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise Exception(f"Keychain lookup failed: {result.stderr.strip()}")
    except Exception as e:
        raise Exception(f"Failed to retrieve credential from keychain: {e}")


def store_keychain_credential(service: str, account: str, password: str) -> None:
    """Store a password in macOS Keychain."""
    try:
        subprocess.run(
            ["security", "add-generic-password", "-s", service, "-a", account, "-w", password],
            capture_output=True, check=True
        )
    except Exception as e:
        raise Exception(f"Failed to store credential in keychain: {e}")


def get_encryption_key() -> bytes:
    """Retrieve encryption key from Keychain or generate new one"""
    try:
        # Try to retrieve existing key from keychain
        key = get_keychain_credential("OndeMonitor", "env_encryption_key")
        if key:
            return base64.urlsafe_b64decode(key)
    except Exception:
        pass
    
    # Generate new key and store it in keychain
    password = os.environ.get("ONDE_MONITOR_PASSWORD", "default_password")
    key = generate_encryption_key(password)
    store_keychain_credential("OndeMonitor", "env_encryption_key", base64.urlsafe_b64encode(key).decode())
    return key


def is_env_file_encrypted(file_path: Path) -> bool:
    """Check if a .env file is encrypted by looking for encryption markers"""
    try:
        with open(file_path, 'rb') as f:
            first_bytes = f.read(10)
            # If file starts with Fernet header (b'gAAAAAB'), it's likely encrypted
            return first_bytes.startswith(b'gAAAAAB')
    except Exception:
        # If we can't read the file or there's an error, assume it's not encrypted
        return False


def encrypt_env_file(content: str) -> bytes:
    """Encrypt environment file content"""
    key = get_encryption_key()
    f = Fernet(key)
    return f.encrypt(content.encode())


def decrypt_env_file(encrypted_content: bytes) -> str:
    """Decrypt environment file content"""
    key = get_encryption_key()
    f = Fernet(key)
    return f.decrypt(encrypted_content).decode()