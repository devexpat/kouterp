# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class Attachment(models.Model):

    _inherit = "ir.attachment"

    # related for backward compatibility with saas-6
    website_url = fields.Char(string="Attachment URL", related='local_url', deprecated=True)

    @api.model
    def get_serving_groups(self):
        return super(Attachment, self).get_serving_groups() + ['website.group_website_designer']
