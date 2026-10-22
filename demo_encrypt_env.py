#!/usr/bin/env python3
"""
Demonstration script for encrypting an existing .env file.
This script shows how to encrypt a current .env file and then verify it works.
"""

import os
import shutil
from pathlib import Path
from env_encryption import encrypt_env_file, is_env_file_encrypted

def demo_encrypt_existing_env():
    """Demonstrate encryption of an existing .env file."""
    
    # Create a sample .env file if one doesn't exist
    env_file = Path(".env")
    
    if not env_file.exists():
        print("Creating sample .env file...")
        sample_content = """CLICKSEND_USERNAME=your-clicksend-email@example.com
CLICKSEND_API_KEY=your-clicksend-api-key
SMS_RECIPIENTS=+61400000000,+61400000001
ONDE_COMPANY_ID=your-onde-company-id"""
        
        with open(env_file, 'w') as f:
            f.write(sample_content)
        print("✓ Sample .env file created")
    
    # Show the original file content
    print("\nOriginal .env file content:")
    with open(env_file, 'r') as f:
        original_content = f.read()
        print(original_content)
    
    # Show that it's not encrypted yet
    if is_env_file_encrypted(env_file):
        print("✓ File is already encrypted")
    else:
        print("✗ File is not encrypted (as expected)")
    
    # Encrypt the file
    print("\nEncrypting .env file...")
    
    # Read the original content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Encrypt it
    encrypted_content = encrypt_env_file(content)
    
    # Write the encrypted content back to file
    with open(env_file, 'wb') as f:
        f.write(encrypted_content)
    
    print("✓ File encrypted successfully")
    
    # Verify it's now encrypted
    if is_env_file_encrypted(env_file):
        print("✓ File is now encrypted (verified)")
    else:
        print("✗ File encryption verification failed")
        return False
    
    # Show the encrypted file looks different
    print("\nEncrypted file content (first 100 bytes):")
    with open(env_file, 'rb') as f:
        encrypted_bytes = f.read(100)
        print(repr(encrypted_bytes))
    
    print("\nDemonstration complete!")
    print("The .env file is now encrypted and will be automatically decrypted when loaded by the scripts.")
    return True

if __name__ == "__main__":
    print("Environment File Encryption Demonstration")
    print("=" * 40)
    
    try:
        demo_encrypt_existing_env()
        print("\n✓ Demonstration completed successfully!")
    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        raise