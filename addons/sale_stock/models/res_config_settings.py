# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    security_lead = fields.Float(related='company_id.security_lead', string="Security Lead Time")
    group_route_so_lines = fields.Boolean("Order-Specific Routes",
        implied_group='sale_stock.group_route_so_lines')
    module_sale_order_dates = fields.Boolean("Delivery Date")
    group_display_incoterm = fields.Boolean("Incoterms", implied_group='sale_stock.group_display_incoterm')
    use_security_lead = fields.Boolean(
        string="Security Lead Time for Sales",
        oldname='default_new_security_lead',
        help="Margin of error for dates promised to customers. Products will be scheduled for delivery that many days earlier than the actual promised date, to cope with unexpected delays in the supply chain.")
    default_picking_policy = fields.Selection([
        ('direct', 'Ship products as soon as available, with back orders'),
        ('one', 'Ship all products at once')
        ], "Shipping Management", default='direct', default_model="sale.order", required=True)

    @api.onchange('use_security_lead')
    def _onchange_use_security_lead(self):
        if not self.use_security_lead:
            self.security_lead = 0.0

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            use_security_lead=self.env['ir.config_parameter'].sudo().get_param('sale_stock.use_security_lead')
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('sale_stock.use_security_lead', self.use_security_lead)
