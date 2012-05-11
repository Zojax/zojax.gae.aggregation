# -*- coding: utf-8 -*-

import sys
import uuid
try:
    import ndb
except ImportError:  # pragma: no cover
    from google.appengine.ext import ndb

# Monkey patch for ndb availability
sys.modules['ndb'] = ndb
################

from ndb import model
from google.appengine.api import memcache, taskqueue
from webapp2 import uri_for


class Aggregation(model.Model):
    """
    Aggregation
    """
    refkey = model.KeyProperty('k', required=True)
    field = model.StringProperty('f', required=True)
    value = model.FloatProperty('v', default=0)

    @classmethod
    def get_aggregation(cls, key, field_name):
        """
        Retrieves aggregation object by provided key and field name.
        """
        cachekey = str(hash(field_name + str(key)))
        aggregation = memcache.get(cachekey)
        if not aggregation:
            aggregation = cls.query(cls.refkey == key, cls.field==field_name, ancestor=key).get()
            if aggregation is not None:
                memcache.add(key=cachekey, value=aggregation)

        return aggregation

    @classmethod
    def set_aggregation(cls, key, field_name, value):
        """
        Updates aggregation object by provided key and field name.
        """
        # Need to execute in task
        taskqueue.add(url=uri_for("aggregation_worker"),
                      transactional=True,
                      params={'key': key.urlsafe(),
                              'field_name': field_name,
                              'value': value,
                              'uuid': uuid.uuid4()
                             })

