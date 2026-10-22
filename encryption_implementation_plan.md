# Encryption Implementation Plan for .env Files

## Current State Analysis

The project currently stores sensitive credentials (ClickSend API key) in plaintext within `.env` files, which poses a security risk. The existing architecture:

1. Three main Python scripts (`onde_monitor.py`, `onde_monitor_firefox.py`, and `onde_monitor_keychain.py`) all use the same `.env` loading mechanism
2. Each script has its own `load_env_file()` function that loads environment variables from a local `.env` file
3. Keychain integration exists for storing/retrieving credentials but is only used in `onde_monitor_keychain.py`
4. The ClickSend API key is loaded directly from the `.env` file in all scripts (not via keychain)
5. There's no encryption mechanism for the .env files

## Security Plan Implementation

### Phase 1: Preparation
- Install required Python packages (`cryptography`, `keyring`)
- Backup existing `.env` file before making changes
- Plan backward compatibility strategy to ensure existing installations continue working

### Phase 2: Key Management 
- Create function to generate encryption key with PBKDF2 using salt
- Integrate with existing keychain infrastructure for key storage/retrieval (consistent with current credential handling patterns)
- Handle key generation when no key exists (using the same approach as existing keychain credentials)

### Phase 3: Encryption Utilities
Implement these functions:
1. `encrypt_env_file(content: str) -> bytes` - Encrypts environment file content
2. `decrypt_env_file(encrypted_content: bytes) -> str` - Decrypts environment file content  
3. `is_env_file_encrypted(file_path: Path) -> bool` - Checks if a file is encrypted
4. `get_encryption_key() -> bytes` - Retrieves encryption key from keychain or generates new one
5. `generate_encryption_key() -> bytes` - Generates new encryption key with PBKDF2

### Phase 4: Integration
Modify `load_env_file()` functions in all three scripts to:
- Check if the .env file is encrypted before processing
- If not encrypted, process as normal (maintaining backward compatibility)
- If encrypted, decrypt the file content and load into environment variables
- Add proper error handling for decryption failures

### Phase 5: Validation
- Test encryption/decryption with sample data
- Verify backward compatibility with existing unencrypted files
- Test error conditions (missing keys, corrupted data)
- Validate Keychain integration works correctly

## Code Modifications Required

### New Functions to Add:
1. `encrypt_env_file(content: str) -> bytes`
2. `decrypt_env_file(encrypted_content: bytes) -> str` 
3. `is_env_file_encrypted(file_path: Path) -> bool`
4. `get_encryption_key() -> bytes`
5. `generate_encryption_key() -> bytes`

### Modified Functions:
1. `load_env_file(path: Path) -> None` - Update to handle encrypted files

## Implementation Approach

1. **Use existing keychain infrastructure** - Leverage the same approach used for credential storage, storing encryption keys in the macOS Keychain
2. **Maintain backward compatibility** - Existing installations with unencrypted .env files should continue working without modification
3. **Follow PBKDF2 + AES-256 pattern** - Use standard cryptographic libraries and practices consistent with security industry standards
4. **Secure key management** - Store encryption keys in the Keychain, similar to how credentials are managed

## Backward Compatibility Strategy

1. The system will detect if a .env file is encrypted or not
2. If unencrypted, process as before (existing behavior)
3. If encrypted, decrypt and process normally
4. Provide a migration path for users to encrypt their files
5. Keep unencrypted backup during transition period

## Deployment Considerations

1. Update documentation with encryption instructions
2. Add warning about not losing the encryption key
3. Document recovery procedures 
4. Ensure scripts work on both new and existing installations
5. Test thoroughly across all three script variants

## Security Measures

1. Use AES-256 encryption (cryptography library default)
2. PBKDF2 key derivation with salt
3. Secure random number generation for keys
4. Proper error handling to avoid information leakage
5. Maintain existing Keychain security controls
6. Ensure all scripts use the same encryption/decryption approach

This implementation maintains all existing functionality while significantly improving security by protecting sensitive credentials in the .env file. The approach leverages the existing Keychain infrastructure, ensuring consistency with the project's current security practices.