# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models


class RemovalStrategy(models.Model):
    _name = 'product.removal'
    _description = 'Removal Strategy'

    name = fields.Char('Name', required=True)
    method = fields.Char("Method", required=True, help="FIFO, LIFO...")


class PutAwayStrategy(models.Model):
    _name = 'product.putaway'
    _description = 'Put Away Strategy'

    name = fields.Char('Name', required=True)
    fixed_location_ids = fields.One2many(
        'stock.fixed.putaway.strat', 'putaway_id', 'Fixed Locations Per Product Category', copy=True,
        help="When the method is fixed, this location will be used to store the products")

    def putaway_apply(self, product):
        for strat in self.fixed_location_ids:
            categ = product.categ_id
            while categ:
                if strat.category_id.id == categ.id:
                    return strat.fixed_location_id
                categ = categ.parent_id
        return self.env['stock.location']


class FixedPutAwayStrategy(models.Model):
    _name = 'stock.fixed.putaway.strat'
    _order = 'sequence'

    putaway_id = fields.Many2one('product.putaway', 'Put Away Method', required=True)
    category_id = fields.Many2one('product.category', 'Product Category', required=True)
    fixed_location_id = fields.Many2one('stock.location', 'Location', required=True)
    sequence = fields.Integer('Priority', help="Give to the more specialized category, a higher priority to have them in top of the list.")
