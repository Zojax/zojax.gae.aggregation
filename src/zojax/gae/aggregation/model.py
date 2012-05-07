# -*- coding: utf-8 -*-

## HACK FOR ndb
import sys
try:
    import ndb
except ImportError:  # pragma: no cover
    from google.appengine.ext import ndb

# Monkey patch for ndb availability
sys.modules['ndb'] = ndb
################

from ndb import model
from google.appengine.api import memcache


class AggregatedProperty(object):
    """
    Model property for aggregation operations.
        * name - property name, required;
        * default - initial value;

    """
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, cls):

        return Aggregation.get_or_create_aggregation(instance.key, self.name).value

    def __set__(self, instance, value):
        import logging; logging.info("__set__ !!!!!!!!!!!!! %s " % str(instance))
        Aggregation.set_aggregation(instance.key, self.name, value)


def sum_add(instance, field, aggregator_instance, aggregator_field):
    """
    Shortcut function for adding sum operation. Requires next arguments:
        * instance - instance of aggregated model;
        * field - name of field the sum is calculated by;
        * aggregator - instance of the AggregatedProperty;

    """
    ndb.get_context().clear_cache()
    old_instance = instance.key.get()
    sum_part = getattr(instance, field)
    if old_instance:
        if getattr(old_instance, field) != getattr(instance, field):
            sum_part -= getattr(old_instance, field)
        else:
            return
    #import pdb; pdb.set_trace()
    setattr(aggregator_instance,
            aggregator_field,
            getattr(aggregator_instance, aggregator_field) + sum_part)



def sum_sub(instance, field, aggregator_instance, aggregator_field):
    """
    Shortcut function for sub sum operation. Requires next arguments:
        * instance - instance of aggregated model;
        * field - name of field the sum is calculated by;
        * aggregator - instance of the AggregatedProperty;

    """
    setattr(aggregator_instance,
            aggregator_field,
            getattr(aggregator_instance, aggregator_field) - getattr(instance, field)
            )


class Aggregation(model.Model):
    """
    Aggregation
    """
    key = model.KeyProperty('k', required=True)
    field = model.StringProperty('f', required=True)
    value = model.FloatProperty('v', default=0)

    @classmethod
    def get_or_create_aggregation(cls, key, field_name):
        """
        Retrieves aggregation object by provided key and field name. When fist time called,
        new aggregation will be created.
        """
        #field = '%s|%s' % (field_name, aggregation_type)
        cachekey = str(hash(field_name + str(key)))
        aggregation = memcache.get(cachekey)
        if not aggregation:
            aggregation = cls.query(cls.key == key, cls.field==field_name).get()
            if not aggregation:
                # Need to execute it in the task
                aggregation = cls(key=key, field=field_name)
                aggregation.put()

            memcache.add(key=cachekey, value=aggregation)

        return aggregation

    @classmethod
    def set_aggregation(cls, key, field_name, value):
        """
        Updates aggregation object by provided key and field name.
        """
        cachekey = str(hash(field_name + str(key)))
        aggregation = cls.get_or_create_aggregation(key, field_name)
        try:
            aggregation.value = float(value)
        except ValueError:
            return
        # Need to execute in task
        aggregation.put()
        memcache.set(cachekey, aggregation)

        return aggregation


#    @property
#    def aggregation_type(self):
#        field_name, aggregation = self.field.split("|")
#
#        return aggregation

#    @property
#    def field_name(self):
#        field_name, aggregation = self.field.split("|")
#
#        return field_name

#    @classmethod
#    def get_or_create_or_set_aggregation(cls, key, field_name, update_value=None):
#        """ doc"""
#        aggregation = cls.query(cls.key == key, cls.field==field_name).get()
#        write = False
#        if not aggregation:
#            # Need to execute it in the task
#            aggregation = cls(key=key, field=field_name)
#            write = True
#        if update_value != None:
#            try:
#                aggregation.value = float(update_value)
#            except ValueError:
#                return
#            write = True
#        if write:
#            aggregation.put()
#        return aggregation

#    @classmethod
#    def inc_count(cls, key, field_name):
#        """
#        Count aggregation: Increments value for provided key and field_name of key's model.
#            * key - key of object aggregation is being created for;
#            * field_name - name of the aggregated field;
#        """
#        aggregation = cls.get_or_create_aggregation(key, field_name, "Count")
#        # Need to use task here
#        aggregation.value += 1
#        aggregation.put()
#
#    @classmethod
#    def dec_count(cls, key, field_name):
#        """
#        Count aggregation: Decrements value for provided key and field_name of key's model.
#            * key - key of object aggregation is being created for;
#            * field_name - name of the aggregated field;
#        """
#        aggregation = cls.get_or_create_aggregation(key, field_name, "Count")
#        # Need to use task here
#        aggregation.value -= 1
#        aggregation.put()
#
#    @classmethod
#    def inc_sum(cls, key, field_name, sum_field, now_sum):
#        """
#        Sum aggregation: Increments sum of value for provided key, field_name, sum_field of key's model.
#            * key - key of object aggregation is being created for;
#            * field_name - name of the aggregated field;
#            * sum_field - name of the field of field_name the sum will be increased by;
#
#        """
#        aggregation = cls.get_or_create_aggregation(key, field_name, "Sum")
#        # Need to use task here
#        aggregation.sum += now_sum
#        aggregation.put()

