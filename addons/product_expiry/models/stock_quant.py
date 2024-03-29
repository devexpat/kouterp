# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    removal_date = fields.Datetime(related='lot_id.removal_date', store=True)

    @api.model
    def _get_removal_strategy_order(self, removal_strategy):
        if removal_strategy == 'fefo':
            return 'removal_date, in_date, id'
        return super(StockQuant, self)._get_removal_strategy_order(removal_strategy)
