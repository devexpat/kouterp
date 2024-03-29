# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra import api, fields, models, tools


class TestMassMailing(models.TransientModel):
    _name = 'mail.mass_mailing.test'
    _description = 'Sample Mail Wizard'

    email_to = fields.Char(string='Recipients', required=True,
                           help='Comma-separated list of email addresses.', default=lambda self: self.env['mail.message']._get_default_from())
    mass_mailing_id = fields.Many2one('mail.mass_mailing', string='Mailing', required=True, ondelete='cascade')

    @api.multi
    def send_mail_test(self):
        self.ensure_one()
        mails = self.env['mail.mail']
        mailing = self.mass_mailing_id
        test_emails = tools.email_split(self.email_to)
        for test_mail in test_emails:
            # Convert links in absolute URLs before the application of the shortener
            mailing.write({'body_html': self.env['mail.template']._replace_local_links(mailing.body_html)})
            mail_values = {
                'email_from': mailing.email_from,
                'reply_to': mailing.reply_to,
                'email_to': test_mail,
                'subject': mailing.name,
                'body_html': tools.html_sanitize(mailing.body_html, sanitize_attributes=True, sanitize_style=True, strip_classes=True),
                'notification': True,
                'mailing_id': mailing.id,
                'attachment_ids': [(4, attachment.id) for attachment in mailing.attachment_ids],
                'auto_delete': True,
            }
            mail = self.env['mail.mail'].create(mail_values)
            mails |= mail
        mails.send()
        return True
