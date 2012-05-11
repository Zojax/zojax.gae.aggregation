# -*- coding: utf-8 -*-

import ndb
from ndb import model

from .model import Aggregation


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


# TODO: Finish check_max function
#def check_max(instance, field, aggregator_instance, aggregator_field, process_func=None, condition_func=None, action="add"):
#    """
#    Shortcut function for maximum adjust operation. Requires next arguments:
#        * instance - instance of aggregated instance model;
#        * field - name of field the sum is calculated by;
#        * aggregator_instance - instance of the model the aggregation created for;
#        * aggregator_field - name of the field of aggregator_instance which is AggregatedProperty;
#        * process_func - input value processing function, usually is a lambda function like lambda x: abs(x);
#        * condition_func - condition function for aggregated instance,
#                            usually is a lambda function like lambda x: x.field_name > some_value;
#        * action - action type on aggregated instance; by default is add, otherwise is interpreted as delete;
#
#    """
#    if condition_func is None:
#        condition_func = lambda x: True
#    if not condition_func(aggregator_instance):
#        return
#    if process_func is None:
#        process_func = lambda x:x
#    current_max = getattr(aggregator_instance, aggregator_field)
#    contender = process_func(getattr(instance, field))
#    if action == "add":
#        if contender > current_max:
#            setattr(aggregator_instance, aggregator_field, contender)
#        return
#    if contender == current_max and action != "add":
#        # TODO: need to filter query additionality by aggregator_instance
#        max_instance = instance.query(instance.__class__.key != instance.key, ancestor=aggregator_instance.key)\
#        .order(-getattr(instance.__class__, field)).fetch(limit=1)
#
#        setattr(aggregator_instance, aggregator_field, process_func(getattr(max_instance, field)))