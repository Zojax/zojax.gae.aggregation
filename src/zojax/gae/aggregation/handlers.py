# -*- coding: utf-8 -*-

import os
import webapp2
import logging

try:
    import ndb
except ImportError: # pragma: no cover
    from google.appengine.ext import ndb


from google.appengine.api import memcache, taskqueue
#from ndb import Key

from zojax.gae.aggregation.model import Aggregation

default_config = {}


class BaseHandler(webapp2.RequestHandler):
    """
         BaseHandler for all requests
    """
    config_key = __name__

    def __init__(self, request=None, response=None):
        super(BaseHandler, self).__init__(request=request, response=response)

        self.config = request.app.config.load_config(self.config_key,
            default_values=default_config,
        )


class AggregationWorker(BaseHandler):

    def post(self):
        #import pdb; pdb.set_trace()
        key = ndb.Key(urlsafe=self.request.get('key'))
        field_name = self.request.get('field_name')
        value = float(self.request.get('value'))
        uuid = float(self.request.get('uuid'))

        duplicated = memcache.get(uuid)
        if duplicated:
            return
        else:
            memcache.set(uuid, 1)

        aggregation = Aggregation.get_aggregation(key, field_name)
        if not aggregation:
            aggregation = Aggregation(refkey=key, field=field_name, parent=key)

        aggregation.value = float(value)
        aggregation.put()

        cachekey = str(hash(field_name + str(key)))
        memcache.set(cachekey, aggregation)
        memcache.delete(uuid)
