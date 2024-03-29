# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    intrastat_product_origin_country_id = fields.Many2one('res.country', string='Origin Country of Product')
