# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    manufacturing_lead = fields.Float(related='company_id.manufacturing_lead', string="Manufacturing Lead Time")
    use_manufacturing_lead = fields.Boolean(string="Default Manufacturing Lead Time", oldname='default_use_manufacturing_lead')
    module_mrp_byproduct = fields.Boolean("By-Products")
    module_mrp_plm = fields.Boolean("Product Lifecycle Management (PLM)")
    module_quality_mrp = fields.Boolean("Quality")
    module_mrp_repair = fields.Boolean("Repair")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            use_manufacturing_lead=self.env['ir.config_parameter'].sudo().get_param('mrp.use_manufacturing_lead')
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('mrp.use_manufacturing_lead', self.use_manufacturing_lead)

    @api.onchange('use_manufacturing_lead')
    def _onchange_use_manufacturing_lead(self):
        if not self.use_manufacturing_lead:
            self.manufacturing_lead = 0.0
