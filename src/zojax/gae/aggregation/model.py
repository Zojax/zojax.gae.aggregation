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




class Aggregation(model.Model):
    """
    Aggregation
    """
    key = model.KeyProperty('k', required=True)
    field = model.StringProperty('f', required=True)
    value = model.FloatProperty('v', required=0)

    @property
    def aggregation_type(self):
        field_name, aggregation = self.field.split("|")

        return aggregation

    @property
    def field_name(self):
        field_name, aggregation = self.field.split("|")

        return field_name

    @classmethod
    def get_or_create_aggregation(cls, key, field_name, aggregation_type):
        """ doc"""
        field = '%s|%s' % (field_name, aggregation_type)
        aggregation = cls.query(cls.key == key, cls.field==field).get()
        if not aggregation:
            # Need to execute it in the task
            aggregation = cls(key=key, field=field)
            aggregation.put()

        return aggregation

    @classmethod
    def inc_count(cls, key, field_name):
        """
        Count aggregation: Increments value for provided key and field_name of key's model.
            * key - key of object aggregation is being created for;
            * field_name - name of the aggregated field;
        """
        aggregation = cls.get_or_create_aggregation(key, field_name, "Count")
        # Need to use task here
        aggregation.value += 1
        aggregation.put()

    @classmethod
    def dec_count(cls, key, field_name):
        """
        Count aggregation: Decrements value for provided key and field_name of key's model.
            * key - key of object aggregation is being created for;
            * field_name - name of the aggregated field;
        """
        aggregation = cls.get_or_create_aggregation(key, field_name, "Count")
        # Need to use task here
        aggregation.value -= 1
        aggregation.put()

    @classmethod
    def inc_sum(cls, key, field_name, sum_field, now_sum):
        """
        Sum aggregation: Increments sum of value for provided key, field_name, sum_field of key's model.
            * key - key of object aggregation is being created for;
            * field_name - name of the aggregated field;
            * sum_field - name of the field of field_name the sum will be increased by;

        """
        aggregation = cls.get_or_create_aggregation(key, field_name, "Sum")
        # Need to use task here
        aggregation.sum += now_sum
        aggregation.put()

