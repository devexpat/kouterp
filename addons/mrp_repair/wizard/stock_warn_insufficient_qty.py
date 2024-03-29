# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models

class StockWarnInsufficientQtyRepair(models.TransientModel):
    _name = 'stock.warn.insufficient.qty.repair'
    _inherit = 'stock.warn.insufficient.qty'

    repair_id = fields.Many2one('mrp.repair', string='Repair')

    def action_done(self):
        self.ensure_one()
        return self.repair_id.action_repair_confirm()
