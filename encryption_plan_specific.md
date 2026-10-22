# Encryption Plan for .env Files - Specific Implementation

## Project Context
This is a Python-based monitoring tool that uses three main scripts:
- `onde_monitor.py` - Main monitor script
- `onde_monitor_firefox.py` - Firefox automation scripts  
- `onde_monitor_keychain.py` - Keychain related functions

All three scripts use a shared `load_env_file()` function to load environment variables from a local `.env` file.

## Current Vulnerability
The ClickSend API key is stored in plaintext within the `.env` file, representing a high security risk. If an attacker gains access to the system, they immediately have access to the credentials.

## Targeted Solution Approach
Implement encryption for the `.env` configuration files using:
1. Symmetric encryption with AES-256 
2. PBKDF2 key derivation for password-based encryption
3. Key storage in macOS Keychain (consistent with existing credential handling patterns)
4. Full backward compatibility to ensure existing installations continue working

## Implementation Steps

### Phase 1: Preparation
- Install required Python packages (`cryptography`, `keyring`)
- Backup existing `.env` file before making changes
- Plan backward compatibility strategy

### Phase 2: Key Management
- Create function to generate encryption key with PBKDF2
- Integrate with existing keychain infrastructure for key storage/retrieval (consistent with current credential handling patterns)
- Handle key generation when no key exists

### Phase 3: Encryption Utilities
Implement these functions in a new module or within the existing scripts:
1. `encrypt_env_file(content: str) -> bytes` - Encrypts environment file content
2. `decrypt_env_file(encrypted_content: bytes) -> str` - Decrypts environment file content  
3. `is_env_file_encrypted(file_path: Path) -> bool` - Checks if a file is encrypted
4. `get_encryption_key() -> bytes` - Retrieves encryption key from keychain or generates new one
5. `generate_encryption_key() -> bytes` - Generates new encryption key with PBKDF2

### Phase 4: Integration
Modify the `load_env_file()` functions in all three scripts to:
- Check if the .env file is encrypted before processing
- If not encrypted, process as normal (maintaining backward compatibility)
- If encrypted, decrypt the file content and load into environment variables
- Add proper error handling for decryption failures

### Phase 5: Validation
- Test encryption/decryption with sample data
- Verify backward compatibility with existing unencrypted files
- Test error conditions (missing keys, corrupted data)
- Validate Keychain integration works correctly

## Detailed Implementation Strategy

### A. Install Dependencies
```bash
pip install cryptography keyring
```

### B. New Module Structure (Recommended Approach)
Create a new file `env_encryption.py` that contains all encryption utilities:
```python
# env_encryption.py
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
    key = generate_encryption_key(os.environ.get("ONDE_MONITOR_PASSWORD", "default_password"))
    store_keychain_credential("OndeMonitor", "env_encryption_key", base64.urlsafe_b64encode(key).decode())
    return key

def is_env_file_encrypted(file_path: Path) -> bool:
    """Check if a .env file is encrypted"""
    # Implementation depends on how we mark encrypted files
    pass

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
```

### C. Modified load_env_file Function
Each script's `load_env_file()` function would be updated to:
```python
def load_env_file(path: Path) -> None:
    """Populate os.environ from a simple KEY=VALUE .env file, if present."""
    if not path.exists():
        return
    
    # Check if file is encrypted
    if is_env_file_encrypted(path):
        # Decrypt and load content
        with open(path, 'rb') as f:
            encrypted_content = f.read()
        decrypted_content = decrypt_env_file(encrypted_content)
        for line in decrypted_content.splitlines():
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())
    else:
        # Load as normal (backward compatibility)
        with open(path, 'r') as f:
            for line in f:
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())
```

## Backward Compatibility
The implementation will:
- Check if `.env` file is encrypted before processing
- If not encrypted, process as normal (existing behavior)
- Add migration path for users to encrypt their files
- Keep unencrypted backup during transition period

## Security Measures
1. Use AES-256 encryption with Fernet (which uses AES-256 in CBC mode)
2. PBKDF2 key derivation with salt and 100,000 iterations
3. Secure random number generation for keys
4. Proper error handling to avoid information leakage
5. Maintain existing Keychain security controls

## Deployment Considerations
1. Update documentation with encryption instructions
2. Add warning about not losing the encryption key
3. Document recovery procedures
4. Ensure scripts work on both new and existing installations