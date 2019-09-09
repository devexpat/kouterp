# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

import flectra.tests


@flectra.tests.common.at_install(False)
@flectra.tests.common.post_install(True)
class TestUi(flectra.tests.HttpCase):

    def test_01_project_tour(self):
        self.phantom_js("/web", "flectra.__DEBUG__.services['web_tour.tour'].run('project_tour')", "flectra.__DEBUG__.services['web_tour.tour'].tours.project_tour.ready", login="admin")
