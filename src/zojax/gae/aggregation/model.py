# -*- coding: utf-8 -*-

## HACK FOR ndb
import sys
import base64
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


class AggregatedProperty(object):
    """
    Model property for aggregation operations.
        * name - property name, required;
        * default - initial value;

    """
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, cls):

        aggregation = Aggregation.get_aggregation(instance.key, self.name)
        if aggregation:
            return aggregation.value

        return 0

    def __set__(self, instance, value):
        Aggregation.set_aggregation(instance.key, self.name, value)


def sum_add(instance, field, aggregator_instance, aggregator_field, process_func=None):
    """
    Shortcut function for adding sum operation. Requires next arguments:
        * instance - instance of aggregated model;
        * field - name of field the sum is calculated by;
        * aggregator_instance - instance of the model the aggregation created for;
        * aggregator_field - name of the field of aggregator_instance which is AggregatedProperty;
        * process_func - input value processing function, usually is a lambda function like lambda x: abs(x);

    """
    if process_func is None:
        process_func = lambda x:x

    ndb.get_context().clear_cache()
    if instance.key.id():
        old_instance = instance.key.get()
    else:
        old_instance = None
    sum_part = process_func(getattr(instance, field))
    if old_instance:
        if process_func(getattr(old_instance, field)) != sum_part:
            sum_part -= process_func(getattr(old_instance, field))
        else:
            return
    #import pdb; pdb.set_trace()
    setattr(aggregator_instance,
            aggregator_field,
            getattr(aggregator_instance, aggregator_field) + sum_part)



def sum_sub(instance, field, aggregator_instance, aggregator_field, process_func=None):
    """
    Shortcut function for sub sum operation. Requires next arguments:
        * instance - instance of aggregated model;
        * field - name of field the sum is calculated by;
        * aggregator_instance - instance of the model the aggregation created for;
        * aggregator_field - name of the field of aggregator_instance which is AggregatedProperty;
        * process_func - input value processing function;

    """
    if process_func is None:
        process_func = lambda x:x

    setattr(aggregator_instance,
            aggregator_field,
            getattr(aggregator_instance, aggregator_field) - process_func(getattr(instance, field))
            )

def count_inc(instance, aggregator_instance, aggregator_field):
    """
    Shortcut function for incrementing count operation. Requires next arguments:
        * instance - instance of aggregated model;
        * aggregator_instance - instance of the model the aggregation created for;
        * aggregator_field - name of the field of aggregator_instance which is AggregatedProperty;

    """
    #import pdb; pdb.set_trace()
    if instance.key.id() is None:
        setattr(aggregator_instance,
            aggregator_field,
            getattr(aggregator_instance, aggregator_field) + 1)

def count_dec(instance, aggregator_instance, aggregator_field):
    """
    Shortcut function for decrementing count operation. Requires next arguments:
        * instance - instance of aggregated model;
        * aggregator_instance - instance of the model the aggregation created for;
        * aggregator_field - name of the field of aggregator_instance which is AggregatedProperty;

    """
    setattr(aggregator_instance,
        aggregator_field,
        getattr(aggregator_instance, aggregator_field) - 1)


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

