"""Testing gae.migration."""

import re
import os
import urlparse
import random
import string

from unittest import TestCase

from ndb import model

from google.appengine.ext import testbed
from webapp2 import WSGIApplication

from webtest import TestApp


#from .. import migrate
#from ..migrate import read_migrations, register_migrations, get_migration_dirs
from . import handlers
from . import routes
from model import AggregatedProperty
#from . import model



app = WSGIApplication()

#for r in routes:
#    app.router.add(r)

class BaseTestCase(TestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()
        app_id = 'myapp'
        os.environ['APPLICATION_ID'] = app_id
        os.environ['HTTP_HOST'] = app_id

        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.testbed.init_taskqueue_stub(root_path=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.app = TestApp(app)

    def get_tasks(self):
        return self.testbed.get_stub("taskqueue").GetTasks("default")

    def submit_deferred(self):
        tasks = self.get_tasks()
        taskq = self.testbed.get_stub("taskqueue")
        taskq.FlushQueue("default")
        while tasks:
            for task in tasks:
                params = task["body"].decode('base64')
                self.app.post(task["url"], params)
            tasks = taskq.GetTasks("default")
            taskq.FlushQueue("default")

    def assertContains(self, first, second, msg=None):
        if not second in getattr(first, 'body', first):
            raise self.failureException,\
            (msg or '%r not in %r' % (second, first.body))
            #import nose; nose.tools.set_trace()


class TestComments(model.Model):
    username = model.StringProperty()
    comment = model.StringProperty()
    r = model.FloatProperty()
    s = model.FloatProperty()
    created = model.DateTimeProperty(auto_now=True)


class TestArticle(model.Model):
    ThisCanvass = AggregatedProperty("product_summary_nisd_sum")
    ThisCanvass = AggregatedProperty("product_summary_nisd_sum")


class AggregationTestCase(BaseTestCase):

    def setUp(self):
        super(AggregationTestCase, self).setUp()


    def testReadMigrations(self):
        self.assertEqual(2,2)