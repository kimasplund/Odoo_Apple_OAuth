# Apple OAuth Provider for Odoo 18.0

This module adds Apple OAuth Provider support to Odoo, allowing users to sign in using their Apple ID.

## Features

- Sign in with Apple integration
- Secure JWT token handling
- Configuration through Odoo settings
- Support for Apple's OAuth 2.0 flow
- Server-to-server notifications for account changes

## Requirements

- Odoo 18.0
- Python packages (install via pip):
  - PyJWT
  - cryptography
  - requests

## Installation

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Place this module in your Odoo addons directory

3. Update the addons list in Odoo

4. Install the module through Odoo's module interface

## Configuration

1. Go to Settings > General Settings > OAuth Providers

2. Configure the following Apple OAuth credentials:
   - Client ID (Services ID from Apple Developer account)
   - Team ID (from Apple Developer account)
   - Key ID (from Apple Developer account)
   - Private Key (the contents of the .p8 file from Apple)

3. The module will automatically configure the OAuth provider with the correct endpoints

## Apple Developer Setup

1. Create an App ID:
   - Go to Certificates, IDs & Profiles in Apple Developer portal
   - Select Identifiers > App IDs
   - Use reverse-domain format (e.g., fi.domain.signin)
   - Enable "Sign In with Apple" capability

2. Create a Services ID:
   - Go to Identifiers > Services IDs
   - Configure domain and callback URL
   - Callback URL: `https://your-odoo-domain/auth_oauth/apple/callback`

3. Create Private Key:
   - Go to Keys section
   - Add new key with "Sign In with Apple" enabled
   - Download the .p8 file (only available once)
   - Note the Key ID

4. Configure Server-to-Server Notifications:
   - In your App ID configuration
   - Set notification URL to: `https://your-odoo-domain/auth_oauth/apple/notify`
   - Ensure your domain has valid SSL (TLS 1.2 or higher)

## Server-to-Server Notifications

The module handles the following Apple notifications:
- Email forwarding changes (enabled/disabled)
- Consent revocation
- Account deletion requests

These notifications help maintain user data accuracy and comply with user privacy choices.

## Security Considerations

- Store your Apple private key securely
- Use HTTPS for your Odoo instance
- Regularly rotate your credentials
- Keep all dependencies up to date
- Ensure your notification endpoint is properly secured

## Author

Kim Asplund (https://asplund.kim)

## License

LGPL-3 