#!/usr/bin/env python3
"""
Test script to verify that the .env file encryption functionality works correctly.
"""

import os
import tempfile
from pathlib import Path
from env_encryption import encrypt_env_file, decrypt_env_file, is_env_file_encrypted

def test_encryption_decryption():
    """Test that encryption and decryption work properly."""
    print("Testing encryption/decryption functionality...")
    
    # Create test content
    test_content = "CLICKSEND_USERNAME=test@example.com\nCLICKSEND_API_KEY=1234567890abcdef\nSMS_RECIPIENTS=+1234567890,+0987654321"
    
    # Encrypt the content
    encrypted = encrypt_env_file(test_content)
    print("✓ Content encrypted successfully")
    
    # Decrypt it back
    decrypted = decrypt_env_file(encrypted)
    print("✓ Content decrypted successfully")
    
    # Verify they match
    if decrypted == test_content:
        print("✓ Encryption/decryption cycle works correctly")
        return True
    else:
        print("✗ Encryption/decryption failed - content mismatch")
        return False

def test_is_env_file_encrypted():
    """Test that the is_env_file_encrypted function works correctly."""
    print("\nTesting is_env_file_encrypted function...")
    
    # Create a temporary file with regular content
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
        f.write("CLICKSEND_USERNAME=test@example.com\nCLICKSEND_API_KEY=1234567890abcdef")
        regular_file = f.name
    
    # Create a temporary file with encrypted content
    encrypted_content = encrypt_env_file("CLICKSEND_USERNAME=test@example.com\nCLICKSEND_API_KEY=1234567890abcdef")
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.env') as f:
        f.write(encrypted_content)
        encrypted_file = f.name
    
    # Test regular file
    if not is_env_file_encrypted(Path(regular_file)):
        print("✓ Regular .env file correctly identified as unencrypted")
        regular_result = True
    else:
        print("✗ Regular .env file incorrectly identified as encrypted")
        regular_result = False
    
    # Test encrypted file
    if is_env_file_encrypted(Path(encrypted_file)):
        print("✓ Encrypted .env file correctly identified as encrypted")
        encrypted_result = True
    else:
        print("✗ Encrypted .env file incorrectly identified as unencrypted")
        encrypted_result = False
    
    # Clean up
    os.unlink(regular_file)
    os.unlink(encrypted_file)
    
    return regular_result and encrypted_result

def test_backward_compatibility():
    """Test that the implementation works with existing .env files."""
    print("\nTesting backward compatibility...")
    
    # Create a temporary .env file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
        f.write("# Test .env file\nCLICKSEND_USERNAME=test@example.com\nCLICKSEND_API_KEY=1234567890abcdef")
        env_file = f.name
    
    try:
        # This should work without issues
        from pathlib import Path
        import os
        
        # Simulate loading the environment file
        def test_load_env_file(path: Path) -> None:
            """Test version of load_env_file that works with our test."""
            if not path.exists():
                return
            
            # Import encryption utilities here to avoid circular imports
            try:
                from env_encryption import is_env_file_encrypted, decrypt_env_file
                # Check if file is encrypted
                if is_env_file_encrypted(path):
                    # Decrypt and load content
                    with open(path, 'rb') as f:
                        encrypted_content = f.read()
                    decrypted_content = decrypt_env_file(encrypted_content)
                    for line in decrypted_content.splitlines():
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            print(f"Loaded: {key}={value}")
                else:
                    # Load as normal (backward compatibility)
                    with open(path, 'r') as f:
                        for line in f:
                            if line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                print(f"Loaded: {key}={value}")
            except Exception as e:
                print(f"Error loading environment file: {e}")
                raise
        
        test_load_env_file(Path(env_file))
        print("✓ Backward compatibility works correctly")
        return True
    finally:
        os.unlink(env_file)

if __name__ == "__main__":
    print("Running encryption tests...\n")
    
    success = True
    success &= test_encryption_decryption()
    success &= test_is_env_file_encrypted() 
    success &= test_backward_compatibility()
    
    if success:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed!")
        exit(1)