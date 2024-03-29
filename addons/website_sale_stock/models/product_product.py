# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models
from flectra.http import request


class ProductProduct(models.Model):
    _inherit = 'product.product'

    cart_qty = fields.Integer(compute='_compute_cart_qty')

    def _compute_cart_qty(self):
        website = request and getattr(request, 'website', None)
        if not website:
            return
        cart = website.sale_get_order()
        for product in self:
            product.cart_qty = sum(cart.order_line.filtered(lambda p: p.product_id.id == product.id).mapped('product_uom_qty')) if cart else 0
