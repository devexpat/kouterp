# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    crm_team_id = fields.Many2one(
        'crm.team', string="Sales Channel", domain=[('team_type', '=', 'pos')],
        default=lambda self: self.env['crm.team'].search([('team_type', '=', 'pos')], limit=1).id,
        help="This Point of sale's sales will be related to this Sales Channel.")
