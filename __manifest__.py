{
    'name': 'Apple OAuth Provider',
    'version': '18.0.1.0.0',
    'category': 'Authentication',
    'summary': 'Sign in with Apple OAuth Provider',
    'description': '''
        This module adds Apple OAuth Provider support to Odoo.
        It allows users to sign in using their Apple ID.
    ''',
    'author': 'Kim Asplund',
    'website': 'https://asplund.kim',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'auth_oauth',
        'web',
    ],
    'data': [
        'data/auth_oauth_provider.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
} 