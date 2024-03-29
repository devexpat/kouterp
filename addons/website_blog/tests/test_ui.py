# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

import flectra.tests


@flectra.tests.common.at_install(False)
@flectra.tests.common.post_install(True)
class TestUi(flectra.tests.HttpCase):
    def test_admin(self):
        self.phantom_js("/", "flectra.__DEBUG__.services['web_tour.tour'].run('blog')", "flectra.__DEBUG__.services['web_tour.tour'].tours.blog.ready", login='admin')
