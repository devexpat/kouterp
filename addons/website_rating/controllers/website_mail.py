# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import http
from flectra.http import request

from flectra.addons.portal.controllers.mail import PortalChatter


class WebsiteRating(PortalChatter):

    @http.route()
    def portal_chatter_init(self, res_model, res_id, domain=False, limit=False, **kwargs):
        result = super(WebsiteRating, self).portal_chatter_init(res_model, res_id, domain=domain, limit=limit, **kwargs)
        # get the rating statistics about the record
        if kwargs.get('rating_include'):
            record = request.env[res_model].browse(res_id)
            if hasattr(record, 'rating_get_stats'):
                result['rating_stats'] = record.rating_get_stats([('website_published', '=', True)])
        return result

    @http.route()
    def portal_message_fetch(self, res_model, res_id, domain=False, limit=False, offset=False, **kw):
        # add 'rating_include' in context, to fetch them in portal_message_format
        if kw.get('rating_include'):
            context = dict(request.context)
            context['rating_include'] = True
            request.context = context
        return super(WebsiteRating, self).portal_message_fetch(res_model, res_id, domain=domain, limit=limit, offset=offset, **kw)
