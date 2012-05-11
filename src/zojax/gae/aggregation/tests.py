# -*- coding: utf-8 -*-

import re
import os
import urlparse
import random
import string
import logging
try:
    import ndb
except ImportError: # pragma: no cover
    from google.appengine.ext import ndb
from unittest import TestCase

from ndb import model

from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util
from google.appengine.api import memcache, taskqueue
from ndb.key import Key


import webapp2
from webapp2 import WSGIApplication


from webtest import TestApp


from . import handlers
from .utils import AggregatedProperty, sum_add, sum_sub, count_inc, count_dec
from .routes import routes
from .model import Aggregation


app = WSGIApplication()

for r in routes:
    app.router.add(r)

test_app =  TestApp(app)


class Article(model.Model):
    content = model.StringProperty()
    created = model.DateTimeProperty(auto_now=True)
    comments_count = AggregatedProperty("article_comment_count")
    total_rating = AggregatedProperty("article_rating_sum")
    max_rating = AggregatedProperty("rating_max")
    min_rating = AggregatedProperty("rating_min")


class Comment(model.Model):
    article = model.KeyProperty(kind=Article)
    body = model.StringProperty()
    rating = model.FloatProperty()
    created = model.DateTimeProperty(auto_now=True)
#    parent = Article()

    def _pre_put_hook(self):
        process_data = lambda x: x if x and x>0 else 0
        sum_add(self, "rating", self.article.get(), 'total_rating', process_data)
        count_inc(self, self.article.get(), 'comments_count')
        #check_max(self, "rating", self.article.get(), 'max_rating', lambda x: x)

    @classmethod
    def _pre_delete_hook(cls, key):
        instance = key.get()
        process_data = lambda x: x if x and x>0 else 0
        sum_sub(instance, "rating", instance.article.get(), 'total_rating', process_data)
        count_dec(instance, instance.article.get(), 'comments_count')
        #check_max(instance, "rating", instance.article.get(), 'max_rating', lambda x: x, action="delete")


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
        # Create a consistency policy that will simulate the High Replication consistency model.
        self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=1)
        # Next, declare which service stubs you want to use.
        # Initialize the datastore stub with this policy.
        self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)
        self.testbed.init_memcache_stub()
        self.testbed.init_mail_stub()
        self.testbed.init_taskqueue_stub(root_path=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.app = test_app

        old_set_aggregation = Aggregation.set_aggregation

        def set_aggregation(cls, key, field_name, value):
            request = webapp2.Request.blank("/")
            request.method = 'GET'
            request.app = self.app.app
            webapp2._local.request = request
            return old_set_aggregation(key, field_name, value)

        Aggregation.set_aggregation = classmethod(set_aggregation)

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

def rand_text(size=100):
    words = []
    for i in range(1, 30):
        words.append(''.join([random.choice(string.ascii_letters+'. ') for s in range(1, random.randrange(1,10))]))
    return " ".join(words)



class AggregationTestCase(BaseTestCase):

    def setUp(self):
        super(AggregationTestCase, self).setUp()
        # Initialising  TestComments  objects

        for i in range(1, 3):
            Article(content = rand_text()).put()
        for i in range(1, 15):
            comment = Comment(article = Article.get_by_id(random.randrange(1,3)).key,
                                   body= rand_text(),
                                   rating= random.randrange(0,11)
                                  )
            ndb.transaction(comment.put, xg=True)
            self.submit_deferred()


        comment = Comment.query(Comment.article == model.Key('Article', 1))
        self.count = comment.count()
        self.total_rating = 0
        for field in comment:
            self.total_rating += field.rating

    #Check adder field
    def test_sum_add(self):
        get_total_sum = Aggregation.query(Aggregation.refkey == model.Key('Article', 1),
                                          Aggregation.field == 'article_rating_sum').get().value
        self.assertEqual(self.total_rating, get_total_sum)

    def test_sum_sub(self):
        comment = Comment.query(Comment.article == model.Key('Article', 1)).get()
        last_rating = comment.rating
        ndb.transaction(comment.key.delete, xg=True)
        self.submit_deferred()
        get_total_sum = Aggregation.query(Aggregation.refkey == model.Key('Article', 1),
                                          Aggregation.field == 'article_rating_sum').get().value
        self.assertEqual(self.total_rating-last_rating, get_total_sum)

    def test_existing_sum_change(self):
        comment = Comment.query(Comment.article == model.Key('Article', 1)).get()
        last_rating = comment.rating
        comment.rating = 7.5
        ndb.transaction(comment.put, xg=True)
        self.submit_deferred()
        get_total_sum = Aggregation.query(Aggregation.refkey == model.Key('Article', 1),
                                      Aggregation.field == 'article_rating_sum').get().value
        get_total_count = Aggregation.query(Aggregation.refkey == model.Key('Article', 1),
                                      Aggregation.field == 'article_comment_count').get().value
        self.assertEqual(self.total_rating - last_rating + comment.rating, get_total_sum)
        self.assertEqual(self.count, get_total_count)

    def test_count_inc(self):
        get_count = Aggregation.query(Aggregation.refkey == model.Key('Article', 1),
                                      Aggregation.field == 'article_comment_count').get().value
        self.assertEqual(self.count, get_count)

    def test_count_dec(self):
        comment = Comment.query(Comment.article == model.Key('Article', 1)).get()
        #1/0
        ndb.transaction(comment.key.delete, xg=True)
        self.submit_deferred()
        get_count = Aggregation.query(Aggregation.refkey == model.Key('Article', 1),
                                      Aggregation.field == 'article_comment_count').get().value
        self.assertEqual(self.count-1, get_count)

    def test_aggretation_tran(self):
        def _put(self, **ctx_options):
            request = webapp2.Request.blank("/")
            request.method = 'GET'
            request.app = test_app.app
            webapp2._local.request = request
            super(self.__class__, self)._put(**ctx_options)
            if self.rating == 3:
                import time; time.sleep(1)

        get_total_sum = Aggregation.query(Aggregation.refkey == model.Key('Article', 1),
            Aggregation.field == 'article_rating_sum').get().value
        get_total_count = Aggregation.query(Aggregation.refkey == model.Key('Article', 1),
            Aggregation.field == 'article_comment_count').get().value
        old_put = Comment.put
        Comment.put = _put
        comment = Comment.query(Comment.article == model.Key('Article', 1)).get()
        comment.rating = 3
        ndb.transaction(comment.put, xg=True)
        self.submit_deferred()
        self.assertEqual(self.total_rating, get_total_sum)
        self.assertEqual(self.count, get_total_count)
        Comment.put = old_put

    def test_duplicated_task_prevention(self):
        request = webapp2.Request.blank("/")
        request.method = 'GET'
        request.app = test_app.app
        webapp2._local.request = request
        from webapp2 import uri_for

        article = Article.get_by_id(1)
        total_sum = article.total_rating
        task_kwargs = {'url': uri_for("aggregation_worker"),
                       'params':{'key': article.key.urlsafe(),
                                'field_name': 'article_rating_sum',
                                'value':10.0+total_sum,
                                'uuid': '7a17004a-954a-4d6e-b5b4-22d10a3d539e'
                                }}

        taskqueue.add(**task_kwargs)
        self.submit_deferred()
        self.assertEqual(article.total_rating, total_sum + 10)
        total_sum = article.total_rating

        taskqueue.add(**task_kwargs)
        self.submit_deferred()
        self.assertEqual(article.total_rating, total_sum)

