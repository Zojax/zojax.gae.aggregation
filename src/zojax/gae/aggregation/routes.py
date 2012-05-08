# -*- coding: utf-8 -*-

from webapp2 import Route

from webapp2_extras.routes import PathPrefixRoute


from ..handlers import QueueHandler, AggregationWorker


routes = [

    Route('/tasks/aggregate/', QueueHandler, name='aggregation_queue'),
    Route('/tasks/worker/', AggregationWorker, name='aggregation_worker'),

    ]

main_route = PathPrefixRoute('/_ah/aggregation', routes)