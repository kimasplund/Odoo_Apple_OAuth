from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    # Apple specific fields
    apple_user_id = fields.Char(
        string='Apple User ID',
        help='Unique identifier from Apple',
        copy=False,
        readonly=True
    )
    apple_private_relay = fields.Boolean(
        string='Uses Apple Private Relay',
        help='Whether this user uses Apple private email relay',
        default=False,
        copy=False,
        readonly=True
    )
    apple_real_email = fields.Char(
        string='Real Email',
        help='Real email if different from private relay email',
        copy=False,
        readonly=True
    )
    email_verified = fields.Boolean(
        string='Email Verified',
        help='Whether the email has been verified by Apple',
        default=False,
        copy=False,
        readonly=True
    )
    middle_name = fields.Char(
        string='Middle Name',
        help='Middle name from Apple ID',
        copy=True
    ) 