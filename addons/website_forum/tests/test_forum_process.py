# Part of Kouterp, Flectra. See LICENSE file for full copyright and licensing details.

import flectra.tests

class TestUi(flectra.tests.HttpCase):

    post_install = True
    at_install = False

    def test_01_admin_forum_tour(self):
        self.phantom_js("/", "flectra.__DEBUG__.services['web_tour.tour'].run('question')", "flectra.__DEBUG__.services['web_tour.tour'].tours.question.ready", login="admin")

    def test_02_demo_question(self):
        with self.cursor() as test_cr:
            env = self.env(cr=test_cr)
            forum = env.ref('website_forum.forum_help')
            demo = env.ref('base.user_demo')
            demo.karma = forum.karma_post + 1
        self.phantom_js("/", "flectra.__DEBUG__.services['web_tour.tour'].run('forum_question')", "flectra.__DEBUG__.services['web_tour.tour'].tours.forum_question.ready", login="demo")
