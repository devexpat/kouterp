# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import fields, models, _
from flectra.exceptions import AccessError


class Digest(models.Model):
    _inherit = 'digest.digest'

    kpi_all_sale_total = fields.Boolean('All Sales')
    kpi_all_sale_total_value = fields.Monetary(compute='_compute_kpi_sale_total_value')

    def _compute_kpi_sale_total_value(self):
        if not self.env.user.has_group('sales_team.group_sale_salesman_all_leads'):
            raise AccessError(_("Do not have access, skip this data for user's digest email"))
        for record in self:
            start, end, company = record._get_kpi_compute_parameters()
            all_channels_sales = self.env['sale.report'].read_group([
                ('confirmation_date', '>=', start),
                ('confirmation_date', '<', end),
                ('company_id', '=', company.id)], ['price_total'], ['price_total'])
            record.kpi_all_sale_total_value = sum([channel_sale['price_total'] for channel_sale in all_channels_sales])

    def compute_kpis_actions(self, company, user):
        res = super(Digest, self).compute_kpis_actions(company, user)
        res['kpi_all_sale_total'] = 'sale.report_all_channels_sales_action&menu_id=%s' % self.env.ref('sale.sale_menu_root').id
        return res
