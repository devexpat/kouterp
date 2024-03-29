# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

import datetime
import logging

import requests
import werkzeug.urls

from ast import literal_eval

from flectra import api, release, SUPERUSER_ID
from flectra.exceptions import UserError
from flectra.models import AbstractModel
from flectra.tools.translate import _
from flectra.tools import config, misc, ustr

_logger = logging.getLogger(__name__)


class PublisherWarrantyContract(AbstractModel):
    _name = "publisher_warranty.contract"

    @api.model
    def _get_message(self):
        Users = self.env['res.users']
        IrParamSudo = self.env['ir.config_parameter'].sudo()

        dbuuid = IrParamSudo.get_param('database.uuid')
        db_create_date = IrParamSudo.get_param('database.create_date')
        limit_date = datetime.datetime.now()
        limit_date = limit_date - datetime.timedelta(15)
        limit_date_str = limit_date.strftime(misc.DEFAULT_SERVER_DATETIME_FORMAT)
        nbr_users = Users.search_count([('active', '=', True)])
        nbr_active_users = Users.search_count([("login_date", ">=", limit_date_str), ('active', '=', True)])
        nbr_share_users = 0
        nbr_active_share_users = 0
        if "share" in Users._fields:
            nbr_share_users = Users.search_count([("share", "=", True), ('active', '=', True)])
            nbr_active_share_users = Users.search_count([("share", "=", True), ("login_date", ">=", limit_date_str), ('active', '=', True)])
        user = self.env.user
        domain = [('application', '=', True), ('state', 'in', ['installed', 'to upgrade', 'to remove'])]
        apps = self.env['ir.module.module'].sudo().search_read(domain, ['name'])
        demo_domain = [('name', 'ilike', 'base'), ('demo', '=', True)]
        demo_data_ids = self.env['ir.module.module'].sudo().search(demo_domain)
        demo_data = True
        if not demo_data_ids:
            demo_data = False
        support_code = IrParamSudo.get_param('database.support_code')

        web_base_url = IrParamSudo.get_param('web.base.url')
        msg = {"dbuuid": dbuuid, "nbr_users": nbr_users,
               "nbr_active_users": nbr_active_users,
               "nbr_share_users": nbr_share_users,
               "nbr_active_share_users": nbr_active_share_users,
               "dbname": self._cr.dbname, "db_create_date": db_create_date,
               "version": release.version, "language": user.lang,
               "web_base_url": web_base_url,
               "apps": [app['name'] for app in apps],
               "support_code": support_code,
               "demo_data": demo_data}
        if user.partner_id.company_id:
            company_id = user.partner_id.company_id
            msg.update(company_id.read(["name", "email", "phone"])[0])
        return msg

    @api.model
    def _get_sys_logs(self):
        """
        Utility method to send a publisher warranty get logs messages.
        """
        msg = self._get_message()
        arguments = {'arg0': ustr(msg), "action": "update"}

        url = config.get("publisher_warranty_url")

        r = requests.post(url, data=arguments, timeout=30)
        r.raise_for_status()
        return literal_eval(r.text)

    @api.multi
    def update_notification(self, cron_mode=True):
        """
        Send a message to Flectra's publisher warranty server to check the
        validity of the contracts, get notifications, etc...

        @param cron_mode: If true, catch all exceptions (appropriate for usage in a cron).
        @type cron_mode: boolean
        """
        try:
            # Code will be execute only if parameter value 'True'
            parameter_id = self.env['ir.config_parameter'].sudo().get_param(
                'base_setup.send_statistics')
            if parameter_id != 'true':
                return True
            try:
                result = self._get_sys_logs()
            except Exception:
                if cron_mode:  # we don't want to see any stack trace in cron
                    return False
                _logger.debug("Exception while sending a get logs messages", exc_info=1)
                raise UserError(_("Error during communication with the publisher warranty server."))
            # old behavior based on res.log; now on mail.message, that is not necessarily installed
            user = self.env['res.users'].sudo().browse(SUPERUSER_ID)
            poster = self.sudo().env.ref('mail.channel_all_employees')
            if not (poster and poster.exists()):
                if not user.exists():
                    return True
                poster = user
            for message in result["messages"]:
                try:
                    poster.message_post(body=message, subtype='mt_comment', partner_ids=[user.partner_id.id])
                except Exception:
                    pass
            if result.get('support_info'):
                # Update expiration date
                set_param = self.env['ir.config_parameter'].sudo().set_param
                set_param('database.expiration_date',
                          result['support_info'].get('expiration_date'))
                set_param('database.expiration_reason',
                          result['support_info'].get('expiration_reason',
                                                     'trial'))
                set_param('database.support_code',
                          result['support_info'].get('support_code'))

        except Exception:
            if cron_mode:
                return False  # we don't want to see any stack trace in cron
            else:
                raise
        return True
