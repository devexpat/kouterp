# -*- coding:utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

import os

from flectra.tools import config
from flectra.addons.l10n_in_hr_payroll.tests.common import TestPaymentAdviceBase


class TestPaymentAdvice(TestPaymentAdviceBase):

    def test_00_payment_advice_flow(self):
        # I create a new Payment Advice with NEFT Transaction Enable
        payment_advice = self.Advice.create({
            'name': 'NEFT Advice',
            'bank_id': self.bank_1.id,
            'line_ids': [(0, 0, {
                    'employee_id': self.employee_fp.id,
                    'name': '90125452552',
                    'ifsc_code': 'abn45215145',
                    'bysal': 25000.00,
                }), (0, 0, {
                    'employee_id': self.employee_al.id,
                    'name': '00014521111232',
                    'ifsc_code': 'sbi45452145',
                    'bysal': 20000.00,
                })],
        })

        # I check that the Payment Advice is in "Draft"
        self.assertEqual(payment_advice.state, 'draft')

        # Now I confirm Payment Advice
        payment_advice.confirm_sheet()

        # I check that the Payment Advice state is "Confirmed"
        self.assertEqual(payment_advice.state, 'confirm')

        # In order to test the PDF report defined on a Payment Advice, we will print a Print Advice Report when NEFT is checked
        data, data_format = self.env.ref('l10n_in_hr_payroll.payroll_advice').render(payment_advice.ids)
        if config.get('test_report_directory'):
            open(os.path.join(config['test_report_directory'], 'l10n_in_hr_payroll_summary_report' + data_format), 'wb+').write(data)
