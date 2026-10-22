# Encryption Plan for .env File

## Overview
Implement encryption for the `.env` configuration file in the onde_monitor project to protect the ClickSend API key from exposure if the system is compromised.

## Current Risk
The ClickSend API key is stored in plaintext within the `.env` file, representing a high security risk. If an attacker gains access to the system, they immediately have access to the credentials.

## Solution Approach
Use symmetric encryption with PBKDF2 key derivation, storing the encryption key in the existing macOS Keychain infrastructure (consistent with current credential handling patterns).

## Implementation Steps

### Phase 1: Preparation
- Install required Python packages (`cryptography`, `keyring`)
- Backup existing `.env` file
- Plan backward compatibility strategy

### Phase 2: Key Management
- Create function to generate encryption key with PBKDF2
- Integrate with existing keychain infrastructure for key storage/retrieval
- Handle key generation when no key exists

### Phase 3: Encryption Utilities
- Implement `encrypt_env_file()` function
- Implement `decrypt_env_file()` function  
- Create utility to check if file is encrypted
- Implement fallback for unencrypted files

### Phase 4: Integration
- Update `load_env_file()` function to handle encrypted files
- Maintain backward compatibility with existing `.env` files
- Add proper error handling for decryption failures
- Test integration with existing keychain credential retrieval

### Phase 5: Validation
- Test encryption/decryption with sample data
- Verify backward compatibility
- Test error conditions (missing keys, corrupted data)
- Validate Keychain integration works correctly
- Perform security review

## Code Modifications Required

### New Functions:
1. `encrypt_env_file(content: str) -> bytes`
2. `decrypt_env_file(encrypted_content: bytes) -> str` 
3. `is_env_file_encrypted(file_path: Path) -> bool`
4. `get_encryption_key() -> bytes`
5. `generate_encryption_key() -> bytes`

### Modified Function:
- `load_env_file(path: Path) -> None`

## Security Measures
- Use AES-256 encryption (cryptography library default)
- PBKDF2 key derivation with salt
- Secure random number generation for keys
- Proper error handling to avoid information leakage
- Maintain existing Keychain security controls

## Backward Compatibility
The implementation will:
- Check if `.env` file is encrypted before processing
- If not encrypted, process as normal (existing behavior)
- Add migration path for users to encrypt their files
- Keep unencrypted backup during transition period

## Deployment Considerations
- Update documentation with encryption instructions
- Add warning about not losing the encryption key
- Document recovery procedures
- Ensure scripts work on both new and existing installations

This approach maintains all existing functionality while significantly improving security by protecting sensitive credentials in the `.env` file. The implementation leverages the existing Keychain infrastructure, ensuring consistency with the project's current security practices.