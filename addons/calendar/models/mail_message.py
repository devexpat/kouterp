# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, models

from flectra.addons.calendar.models.calendar import get_real_ids

from flectra.tools import pycompat


class Message(models.Model):

    _inherit = "mail.message"

    @api.model
    def search(self, args, offset=0, limit=0, order=None, count=False):
        """ Convert the search on real ids in the case it was asked on virtual ids, then call super() """
        args = list(args)
        for index in range(len(args)):
            if args[index][0] == "res_id":
                if isinstance(args[index][2], pycompat.string_types):
                    args[index] = (args[index][0], args[index][1], get_real_ids(args[index][2]))
                elif isinstance(args[index][2], list):
                    args[index] = (args[index][0], args[index][1], [get_real_ids(x) for x in args[index][2]])
        return super(Message, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def _find_allowed_model_wise(self, doc_model, doc_dict):
        if doc_model == 'calendar.event':
            order = self._context.get('order', self.env[doc_model]._order)
            for virtual_id in self.env[doc_model].browse(doc_dict).get_recurrent_ids([], order=order):
                doc_dict.setdefault(virtual_id, doc_dict[get_real_ids(virtual_id)])
        return super(Message, self)._find_allowed_model_wise(doc_model, doc_dict)
