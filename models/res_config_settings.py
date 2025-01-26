from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auth_oauth_apple_client_id = fields.Char(
        string='Apple Client ID',
        config_parameter='auth_oauth.apple_client_id'
    )
    auth_oauth_apple_team_id = fields.Char(
        string='Apple Team ID',
        config_parameter='auth_oauth.apple_team_id'
    )
    auth_oauth_apple_key_id = fields.Char(
        string='Apple Key ID',
        config_parameter='auth_oauth.apple_key_id'
    )
    auth_oauth_apple_private_key = fields.Text(
        string='Apple Private Key',
        config_parameter='auth_oauth.apple_private_key'
    ) 