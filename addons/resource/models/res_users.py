# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    resource_ids = fields.One2many(
        'resource.resource', 'user_id', 'Resources')
    resource_calendar_id = fields.Many2one(
        'resource.calendar', 'Default Working Hours',
        related='resource_ids.calendar_id')
