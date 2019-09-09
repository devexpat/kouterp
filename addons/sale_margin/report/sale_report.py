# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    margin = fields.Float('Margin')

    def _select(self):
        return super(SaleReport, self)._select() + ", SUM(l.margin / COALESCE(cr.rate, 1.0)) AS margin"
