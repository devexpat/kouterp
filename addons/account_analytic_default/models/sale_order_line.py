# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        default_analytic_account = self.env['account.analytic.default'].account_get(self.product_id.id, self.order_id.partner_id.id, self.order_id.user_id.id, fields.Date.today())
        if default_analytic_account:
            res.update({'account_analytic_id': default_analytic_account.analytic_id.id})
        return res
