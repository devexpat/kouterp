# -*- coding: utf-8 -*-
# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

from werkzeug import urls

from flectra import api, fields, models
from flectra.tools.translate import html_translate


class RecruitmentSource(models.Model):
    _inherit = 'hr.recruitment.source'

    url = fields.Char(compute='_compute_url', string='Url Parameters')

    @api.one
    @api.depends('source_id', 'source_id.name', 'job_id')
    def _compute_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for source in self:
            source.url = urls.url_join(base_url, "%s?%s" % (source.job_id.website_url,
                urls.url_encode({
                    'utm_campaign': self.env.ref('hr_recruitment.utm_campaign_job').name,
                    'utm_medium': self.env.ref('utm.utm_medium_website').name,
                    'utm_source': source.source_id.name
                })
            ))


class Applicant(models.Model):

    _inherit = 'hr.applicant'

    website_id = fields.Many2one('website', string="Website")

    def website_form_input_filter(self, request, values):
        if 'partner_name' in values:
            values.setdefault('name', '%s\'s Application' % values['partner_name'])
        return values


class Job(models.Model):

    _name = 'hr.job'
    _inherit = ['hr.job', 'website.seo.metadata', 'website.published.mixin']

    def _get_default_website_description(self):
        default_description = self.env["ir.model.data"].xmlid_to_object("website_hr_recruitment.default_website_description")
        return (default_description.render() if default_description else "")

    def _default_website(self):
        default_website_id = self.env.ref('website.default_website')
        return [default_website_id.id] if default_website_id else None

    website_description = fields.Html('Website description', translate=html_translate, sanitize_attributes=False, default=_get_default_website_description)
    website_ids = fields.Many2many('website', 'website_hr_job_pub_rel',
                                   'website_id', 'job_id',
                                   default=_default_website,
                                   string='Websites', copy=False,
                                   help='List of websites in which Job '
                                        'will published.')

    @api.multi
    def _compute_website_url(self):
        super(Job, self)._compute_website_url()
        for job in self:
            job.website_url = "/jobs/detail/%s" % job.id

    @api.multi
    def set_open(self):
        self.write({'website_published': False})
        return super(Job, self).set_open()
