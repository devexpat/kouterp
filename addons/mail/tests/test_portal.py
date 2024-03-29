# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from flectra.addons.mail.tests.common import TestMail
from flectra.tools.misc import mute_logger


class TestPortal(TestMail):

    def test_mail_compose_access_rights(self):
        test_channel = self.env['mail.channel'].create({
            'name': 'Pigs',
            'public': 'groups',
            'group_public_id': self.env.ref('base.group_portal').id})
        port_msg = test_channel.message_post(body='Message')

        # Do: Chell comments Pigs, ok because can write on it (public group)
        test_channel.sudo(self.user_portal).message_post(body='I love Pigs', message_type='comment', subtype='mail.mt_comment')
        # Do: Chell creates a mail.compose.message record on Pigs, because he uses the wizard
        compose = self.env['mail.compose.message'].with_context({
            'default_composition_mode': 'comment',
            'default_model': 'mail.channel',
            'default_res_id': test_channel.id
        }).sudo(self.user_portal).create({
            'subject': 'Subject',
            'body': 'Body text',
            'partner_ids': []})
        compose.send_mail()

        # Do: Chell replies to a Pigs message using the composer
        compose = self.env['mail.compose.message'].with_context({
            'default_composition_mode': 'comment',
            'default_parent_id': port_msg.id
        }).sudo(self.user_portal).create({
            'subject': 'Subject',
            'body': 'Body text'})
        compose.send_mail()

    @mute_logger('flectra.addons.mail.models.mail_mail')
    def test_invite_email_portal(self):
        test_record = self.env['mail.test'].create({'name': 'Pigs'})

        base_url = self.env['ir.config_parameter'].get_param('web.base.url', default='')
        # Carine Poilvache, with email, should receive emails for comments and emails
        partner_carine = self.env['res.partner'].create({'name': 'Carine Poilvache', 'email': 'c@c'})

        # Do: create a mail_wizard_invite, validate it
        self._init_mock_build_email()
        mail_invite = self.env['mail.wizard.invite'].with_context({
            'default_res_model': 'mail.test',
            'default_res_id': test_record.id}).create({
            'partner_ids': [(4, partner_carine.id)], 'send_mail': True})
        mail_invite.add_followers()
        # Test: Pigs followers should contain Admin and Bert
        self.assertIn(partner_carine, test_record.message_partner_ids)
        # Test: partner must have been prepared for signup
        # TDE FIXME: invite email for portal users should be fixed / improved / rethought
        # self.assertTrue(partner_carine.signup_valid, 'partner has not been prepared for signup')
        # self.assertTrue(base_url in partner_carine.signup_url, 'signup url is incorrect')
        # self.assertTrue(self.env.cr.dbname in partner_carine.signup_url, 'signup url is incorrect')
        # self.assertTrue(partner_carine.signup_token in partner_carine.signup_url, 'signup url is incorrect')
        # Test: (pretend to) send email and check subject, body
        self.assertEqual(len(self._mails), 1, 'sent email number incorrect, should be only for Bert')
        for sent_email in self._mails:
            self.assertEqual(
                sent_email.get('subject'), 'Invitation to follow %s: Pigs' % self.env['mail.test']._description,
                'invite: subject of invitation email is incorrect')
            self.assertIn(
                'Administrator invited you to follow %s document: Pigs' % self.env['mail.test']._description, sent_email.get('body'),
                'invite: body of invitation email is incorrect')
            # self.assertIn(
            #     partner_carine.signup_token, sent_email.get('body'),
            #     'invite: body of invitation email does not contain signup token')
