# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import models, api


class event_confirm(models.TransientModel):
    """Event Confirmation"""
    _name = "event.confirm"

    @api.multi
    def confirm(self):
        events = self.env['event.event'].browse(self._context.get('event_ids', []))
        events.do_confirm()
        return {'type': 'ir.actions.act_window_close'}
