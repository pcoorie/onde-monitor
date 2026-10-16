#!/bin/bash

# Setup script to add ClickSend credentials to macOS Keychain
# Run this from the onde_monitor directory

echo "Setting up ClickSend credentials in macOS Keychain..."

# Check if we have the API key from .env file
if [ -f ".env" ]; then
    API_KEY=$(grep "CLICKSEND_API_KEY=" .env | cut -d'=' -f2-)
    USERNAME=$(grep "CLICKSEND_USERNAME=" .env | cut -d'=' -f2-)
    
    if [ ! -z "$API_KEY" ] && [ ! -z "$USERNAME" ]; then
        echo "Found credentials in .env file:"
        echo "  Username: $USERNAME"
        echo "  API Key:  $API_KEY"
        
        # Add to keychain
        echo "Adding username to keychain..."
        security add-generic-password -s "ClickSend" -a "$USERNAME" -p "$USERNAME" -T /usr/bin/security
        
        echo "Adding API key to keychain..."
        security add-generic-password -s "ClickSend" -a "${USERNAME}-api-key" -p "$API_KEY" -T /usr/bin/security
        
        echo ""
        echo "Credentials added successfully!"
        echo ""
        echo "Verification:"
        echo "Username from keychain:"
        security find-generic-password -s "ClickSend" -a "$USERNAME" -w
        echo "API Key from keychain:" 
        security find-generic-password -s "ClickSend" -a "${USERNAME}-api-key" -w
    else
        echo "Error: Could not extract credentials from .env file"
        exit 1
    fi
else
    echo "Error: .env file not found in current directory"
    exit 1
fi

echo ""
echo "Setup complete. You can now run the updated script:"
echo "python3 onde_monitor_keychain.py"