import json
import jwt
import requests
import time
import hmac
import hashlib
import base64
from datetime import datetime, timedelta

from odoo import http
from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.http import request


class AppleOAuthLogin(OAuthLogin):

    def _get_apple_oauth_client_id(self):
        return request.env['ir.config_parameter'].sudo().get_param('auth_oauth.apple_client_id')

    def _get_apple_oauth_team_id(self):
        return request.env['ir.config_parameter'].sudo().get_param('auth_oauth.apple_team_id')

    def _get_apple_oauth_key_id(self):
        return request.env['ir.config_parameter'].sudo().get_param('auth_oauth.apple_key_id')

    def _get_apple_oauth_private_key(self):
        return request.env['ir.config_parameter'].sudo().get_param('auth_oauth.apple_private_key')

    def _update_user_from_apple_data(self, user, apple_data):
        """Update Odoo user with data from Apple."""
        if not user or not apple_data:
            return

        # Get name components from Apple data
        name_data = apple_data.get('name', {})
        if isinstance(name_data, str):
            try:
                name_data = json.loads(name_data)
            except Exception as e:
                name_data = {}

        # Build full name from components
        first_name = name_data.get('firstName', '')
        middle_name = name_data.get('middleName', '')
        last_name = name_data.get('lastName', '')
        name_parts = list(filter(None, [first_name, middle_name, last_name]))
        full_name = ' '.join(name_parts)

        # Update user data if provided by Apple
        vals = {}
        
        # Basic user information
        if full_name:
            vals['name'] = full_name
        if apple_data.get('email'):
            vals['email'] = apple_data['email']
            # Set login to email if it's a new user (login is empty)
            if not user.login:
                vals['login'] = apple_data['email']
        
        # Name components
        if first_name:
            vals['firstname'] = first_name
        if last_name:
            vals['lastname'] = last_name
        if middle_name:
            vals['middle_name'] = middle_name  # If your Odoo has this field
            
        # Apple specific identifiers
        if apple_data.get('sub'):  # Apple's unique user identifier
            vals['apple_user_id'] = apple_data['sub']
        
        # Email verification status
        if apple_data.get('email_verified'):
            vals['email_verified'] = apple_data['email_verified']
            
        # Locale/Language preference if available
        if apple_data.get('locale'):
            # Convert Apple locale format to Odoo language format
            locale = apple_data['locale'].replace('-', '_')
            lang = request.env['res.lang'].sudo().search([
                ('code', '=', locale)
            ], limit=1)
            if lang:
                vals['lang'] = lang.code
                
        # Is private email relay
        if apple_data.get('is_private_email'):
            vals['apple_private_relay'] = True
            
        # Real email (if provided and different from private relay)
        if apple_data.get('real_email'):
            vals['apple_real_email'] = apple_data['real_email']

        if vals:
            user.sudo().write(vals)

    def _generate_client_secret(self):
        """Generate the client secret for Apple OAuth."""
        team_id = self._get_apple_oauth_team_id()
        key_id = self._get_apple_oauth_key_id()
        private_key = self._get_apple_oauth_private_key()
        client_id = self._get_apple_oauth_client_id()

        if not all([team_id, key_id, private_key, client_id]):
            return False

        headers = {
            'kid': key_id,
            'alg': 'ES256'
        }

        payload = {
            'iss': team_id,
            'iat': int(time.time()),
            'exp': int(time.time() + 86400 * 180),  # 180 days
            'aud': 'https://appleid.apple.com',
            'sub': client_id,
        }

        try:
            client_secret = jwt.encode(
                payload=payload,
                key=private_key,
                algorithm='ES256',
                headers=headers
            )
            return client_secret
        except Exception as e:
            request.env['ir.logging'].sudo().create({
                'name': 'apple_oauth',
                'type': 'server',
                'level': 'error',
                'message': str(e),
                'path': 'controllers/main.py',
                'func': '_generate_client_secret',
                'line': '1'
            })
            return False

    @http.route('/auth_oauth/apple/callback', type='http', auth='none')
    def apple_callback(self, **kw):
        """Handle the callback from Apple OAuth."""
        if kw.get('error'):
            return request.render('auth_oauth.oauth_error', {'error': kw.get('error')})

        code = kw.get('code')
        if not code:
            return request.render('auth_oauth.oauth_error', {'error': 'No authorization code received'})

        client_secret = self._generate_client_secret()
        if not client_secret:
            return request.render('auth_oauth.oauth_error', {'error': 'Failed to generate client secret'})

        # Exchange the authorization code for tokens
        token_url = 'https://appleid.apple.com/auth/token'
        data = {
            'client_id': self._get_apple_oauth_client_id(),
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': request.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/auth_oauth/apple/callback'
        }

        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            tokens = response.json()
        except Exception as e:
            return request.render('auth_oauth.oauth_error', {'error': str(e)})

        # Decode the ID token to get user information
        try:
            id_token = tokens.get('id_token')
            user_data = jwt.decode(id_token, options={'verify_signature': False})
        except Exception as e:
            return request.render('auth_oauth.oauth_error', {'error': str(e)})

        # Get additional user data from the user field if present
        user_info = kw.get('user')
        if user_info:
            try:
                additional_data = json.loads(user_info)
                user_data.update(additional_data)
            except:
                pass

        # Create OAuth validation endpoint URL with user data
        provider = request.env.ref('apple_auth_provider.provider_apple')
        validation_url = provider.validation_endpoint
        params = {
            'access_token': tokens.get('access_token'),
            'id_token': id_token,
            'user': json.dumps(user_data)
        }

        # Get or create Odoo user
        validation_response = self.validate_callback(provider.id, validation_url, params)
        
        # Update user data if login successful
        if hasattr(request, 'uid') and request.uid:
            user = request.env['res.users'].sudo().browse(request.uid)
            self._update_user_from_apple_data(user, user_data)

        return validation_response 

    def _verify_apple_notification(self, payload, signature, timestamp):
        """Verify Apple server-to-server notification."""
        if not all([payload, signature, timestamp]):
            return False

        # Get Apple private key
        private_key = self._get_apple_oauth_private_key()
        if not private_key:
            return False

        # Create signing key
        signing_key = f"{timestamp}.{payload}"
        
        # Calculate expected signature
        expected_signature = base64.b64encode(
            hmac.new(
                private_key.encode('utf-8'),
                signing_key.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

        return hmac.compare_digest(signature, expected_signature)

    def _handle_apple_notification(self, notification_type, sub, email):
        """Handle different types of Apple notifications."""
        if not sub:  # sub is Apple's user identifier
            return False

        user = request.env['res.users'].sudo().search([
            ('apple_user_id', '=', sub)
        ], limit=1)

        if not user:
            return False

        if notification_type == 'email-disabled':
            # User disabled email forwarding
            user.write({
                'apple_private_relay': False,
                'apple_real_email': False
            })
        elif notification_type == 'email-enabled':
            # User enabled email forwarding
            user.write({
                'apple_private_relay': True,
                'email': email
            })
        elif notification_type == 'consent-revoked':
            # User revoked consent
            user.write({
                'active': False,
                'apple_private_relay': False,
                'apple_real_email': False
            })
        elif notification_type == 'account-delete':
            # User requested account deletion
            user.unlink()

        return True

    @http.route('/auth_oauth/apple/notify', type='json', auth='none', csrf=False)
    def apple_notification(self):
        """Handle Apple server-to-server notifications."""
        try:
            # Get notification data
            payload = request.jsonrequest
            if not payload:
                return {'status': 'error', 'message': 'No payload received'}

            # Verify notification authenticity
            apple_signature = request.httprequest.headers.get('X-Apple-Signature')
            timestamp = request.httprequest.headers.get('X-Apple-Timestamp')
            
            if not self._verify_apple_notification(
                json.dumps(payload), apple_signature, timestamp
            ):
                return {'status': 'error', 'message': 'Invalid signature'}

            # Process the notification
            events = payload.get('events', {})
            for event_type, event_data in events.items():
                self._handle_apple_notification(
                    event_type,
                    event_data.get('sub'),
                    event_data.get('email')
                )

            return {'status': 'success'}

        except Exception as e:
            request.env['ir.logging'].sudo().create({
                'name': 'apple_oauth',
                'type': 'server',
                'level': 'error',
                'message': f'Notification error: {str(e)}',
                'path': 'controllers/main.py',
                'func': 'apple_notification',
                'line': '1'
            })
            return {'status': 'error', 'message': str(e)} 