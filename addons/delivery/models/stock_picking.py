# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import models, fields, api, _
from flectra.exceptions import UserError

from flectra.addons import decimal_precision as dp


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    @api.one
    @api.depends('quant_ids')
    def _compute_weight(self):
        weight = 0.0
        if self.env.context.get('picking_id'):
            for ml in self.current_picking_move_line_ids:
                weight += ml.product_uom_id._compute_quantity(ml.qty_done,ml.product_id.uom_id) * ml.product_id.weight
        else:
            for quant in self.quant_ids:
                weight += quant.quantity * quant.product_id.weight
        self.weight = weight

    weight = fields.Float(compute='_compute_weight')
    shipping_weight = fields.Float(string='Shipping Weight', help="Can be changed during the 'put in pack' to adjust the weight of the shipping.")


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.multi
    def manage_package_type(self):
        self.ensure_one()
        view_id = self.env.ref('delivery.choose_delivery_package_view_form').id
        return {
            'name': _('Package Details'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'choose.delivery.package',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_stock_quant_package_id': self.result_package_id.id,
                'current_package_carrier_type': self.picking_id.carrier_id.delivery_type if self.picking_id.carrier_id.delivery_type not in ['base_on_rule', 'fixed'] else 'none',
                }
        }


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _default_uom(self):
        weight_uom_id = self.env.ref('product.product_uom_kgm', raise_if_not_found=False)
        if not weight_uom_id:
            uom_categ_id = self.env.ref('product.product_uom_categ_kgm').id
            weight_uom_id = self.env['product.uom'].search([('category_id', '=', uom_categ_id), ('factor', '=', 1)], limit=1)
        return weight_uom_id

    @api.one
    @api.depends('move_line_ids')
    def _compute_packages(self):
        self.ensure_one()
        packs = set()
        for move_line in self.move_line_ids:
            if move_line.result_package_id:
                packs.add(move_line.result_package_id.id)
        self.package_ids = list(packs)

    @api.one
    @api.depends('move_line_ids')
    def _compute_bulk_weight(self):
        weight = 0.0
        for move_line in self.move_line_ids:
            if move_line.product_id and not move_line.result_package_id:
                weight += move_line.product_uom_id._compute_quantity(move_line.qty_done, move_line.product_id.uom_id) * move_line.product_id.weight
        self.weight_bulk = weight

    @api.one
    @api.depends('package_ids', 'weight_bulk')
    def _compute_shipping_weight(self):
        self.shipping_weight = self.weight_bulk + sum([pack.shipping_weight for pack in self.package_ids])

    carrier_price = fields.Float(string="Shipping Cost")
    delivery_type = fields.Selection(related='carrier_id.delivery_type', readonly=True)
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier")
    volume = fields.Float(copy=False)
    weight = fields.Float(compute='_cal_weight', digits=dp.get_precision('Stock Weight'), store=True)
    carrier_tracking_ref = fields.Char(string='Tracking Reference', copy=False)
    carrier_tracking_url = fields.Char(string='Tracking URL', compute='_compute_carrier_tracking_url')
    number_of_packages = fields.Integer(string='Number of Packages', copy=False)
    weight_uom_id = fields.Many2one('product.uom', string='Unit of Measure', required=True, readonly="1", help="Unit of measurement for Weight", default=_default_uom)
    package_ids = fields.Many2many('stock.quant.package', compute='_compute_packages', string='Packages')
    weight_bulk = fields.Float('Bulk Weight', compute='_compute_bulk_weight')
    shipping_weight = fields.Float("Weight for Shipping", compute='_compute_shipping_weight')

    @api.depends('carrier_id', 'carrier_tracking_ref')
    def _compute_carrier_tracking_url(self):
        for picking in self:
            picking.carrier_tracking_url = picking.carrier_id.get_tracking_link(picking) if picking.carrier_id and picking.carrier_tracking_ref else False

    @api.depends('product_id', 'move_lines')
    def _cal_weight(self):
        for picking in self:
            picking.weight = sum(move.weight for move in picking.move_lines if move.state != 'cancel')

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        for pick in self:
            if pick.carrier_id:
                if pick.carrier_id.integration_level == 'rate_and_ship':
                    pick.send_to_shipper()
                pick._add_delivery_cost_to_so()
        return res

    @api.multi
    def put_in_pack(self):
        if self.carrier_id and self.carrier_id.delivery_type not in ['base_on_rule', 'fixed']:
            view_id = self.env.ref('delivery.choose_delivery_package_view_form').id
            return {
                'name': _('Package Details'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'choose.delivery.package',
                'view_id': view_id,
                'views': [(view_id, 'form')],
                'target': 'new',
                'context': {
                    'current_package_carrier_type': self.carrier_id.delivery_type,
                }
            }
        else:
            return self._put_in_pack()

    @api.multi
    def action_send_confirmation_email(self):
        self.ensure_one()
        delivery_template_id = self.env.ref('delivery.mail_template_data_delivery_confirmation').id
        compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        ctx = dict(
            default_composition_mode='comment',
            default_res_id=self.id,
            default_model='stock.picking',
            default_use_template=bool(delivery_template_id),
            default_template_id=delivery_template_id,
            custom_layout='delivery.mail_template_data_delivery_notification'
        )
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def send_to_shipper(self):
        self.ensure_one()
        res = self.carrier_id.send_shipping(self)[0]
        if self.carrier_id.free_over and self.sale_id and self.sale_id._compute_amount_total_without_delivery() >= self.carrier_id.amount:
            res['exact_price'] = 0.0
        self.carrier_price = res['exact_price']
        if res['tracking_number']:
            self.carrier_tracking_ref = res['tracking_number']
        order_currency = self.sale_id.currency_id or self.company_id.currency_id
        msg = _("Shipment sent to carrier %s for shipping with tracking number %s<br/>Cost: %.2f %s") % (self.carrier_id.name, self.carrier_tracking_ref, self.carrier_price, order_currency.name)
        self.message_post(body=msg)

    @api.multi
    def _add_delivery_cost_to_so(self):
        self.ensure_one()
        sale_order = self.sale_id
        if sale_order.invoice_shipping_on_delivery:
            sale_order._create_delivery_line(self.carrier_id, self.carrier_price)

    @api.multi
    def open_website_url(self):
        self.ensure_one()
        if not self.carrier_tracking_url:
            raise UserError(_("Your delivery method has no redirect on courier provider's website to track this order."))

        client_action = {'type': 'ir.actions.act_url',
                         'name': "Shipment Tracking Page",
                         'target': 'new',
                         'url': self.carrier_tracking_url,
                         }
        return client_action

    @api.one
    def cancel_shipment(self):
        self.carrier_id.cancel_shipment(self)
        msg = "Shipment %s cancelled" % self.carrier_tracking_ref
        self.message_post(body=msg)
        self.carrier_tracking_ref = False

    @api.multi
    def check_packages_are_identical(self):
        '''Some shippers require identical packages in the same shipment. This utility checks it.'''
        self.ensure_one()
        if self.package_ids:
            packages = [p.packaging_id for p in self.package_ids]
            if len(set(packages)) != 1:
                package_names = ', '.join([str(p.name) for p in packages])
                raise UserError(_('You are shipping different packaging types in the same shipment.\nPackaging Types: %s' % package_names))
        return True


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        # Prevent copy of the carrier and carrier price when generating return picking
        # (we have no integration of returns for now)
        new_picking, pick_type_id = super(StockReturnPicking, self)._create_returns()
        picking = self.env['stock.picking'].browse(new_picking)
        picking.write({'carrier_id': False,
                       'carrier_price': 0.0})
        return new_picking, pick_type_id
