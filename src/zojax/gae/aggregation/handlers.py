# -*- coding: utf-8 -*-

import os
import webapp2, ndb
import logging

from google.appengine.api import memcache, taskqueue
from ndb import Key

from zojax.gae.aggregation.model import Aggregation



class BaseHandler(webapp2.RequestHandler):
    """
         BaseHandler for all requests

         Holds the auth and session properties so they are reachable for all requests
     """
    config_key = __name__

    def __init__(self, request=None, response=None):
        super(BaseHandler, self).__init__(request=request, response=response)

        self.config = request.app.config.load_config(self.config_key,
            default_values=default_config,
        )


#    @webapp2.cached_property
#    def jinja2(self):
#        # Returns a Jinja2 renderer cached in the app registry.
#        return jinja2.get_jinja2(app=self.app)

#    def render_response(self, _template, **context):
#        # Renders a template and writes the result to the response.
#
#        context["request"] = self.request
#        context["uri_for"] = self.uri_for
#
#        rv = self.jinja2.render_template(_template, **context)
#
#        self.response.write(rv)



#class QueueHandler(BaseHandler):
#    """
#    Puts migrations into task queue.
#    """
#
#    def get(self):
#
#        action = self.request.GET.get("action")
#        target_index = self.request.GET.get("index", None)
#        application = self.request.GET.get("app")
#
#        call_next(self.migrations, application, target_index, action, self.uri_for("migration_worker"))
#
#        self.redirect_to("migration")
#
#        return


class AggregationWorker(BaseHandler):

    def post(self):
        key = Key(self.request.get('key'))
        field_name = self.request.get('field_name')
        value = float(self.request.get('value'))

        aggregation = Aggregation.get_aggregation(key, field_name)
        if not aggregation:
            aggregation = Aggregation(key=key, field=field_name)

        aggregation.value = float(value)
        aggregation.put()

        cachekey = str(hash(field_name + str(key)))
        memcache.set(cachekey, aggregation)
