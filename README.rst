zojax.gae.aggregation
=====================

This package makes google datastore aggregation operations possible

============
Installation
============

Install the package zojax.gae.aggregation into your project.

Add appropriate settings to your yaml config, for example::

    handlers:

    - url: /_ah/aggregation/.*
      script: yourapp.app
      login: admin

    - url: .*
      script: yourapp.app

Also you need to include zojax.gae.aggregation's routes in your application like this::

    from zojax.gae.aggregation.routes import main_route as aggregation_route

    routes = [
                #Your routes list here
                ...
                aggregation_route,
    ]


Usage
-----

Here is an example of aggregations use case: We have Article it's Comments. We need to caclulate average rating
for each article. An example of code will look like this::

    from ndb import model
    from zojax.gae.model import sum_add, sum_sub, count_inc, count_dec

    class Article(model.Model):
        content = model.StringProperty()
        created = model.DateTimeProperty(auto_now=True)
        comments_count = AggregatedProperty("article_comment_count")
        total_rating = AggregatedProperty("article_rating_sum")

        @property
        def average_rating(self):
            return self.total_rating / self.comments_count


    class Comment(model.Model):
        article = model.KeyProperty(kind=Article)
        body = model.StringProperty()
        rating = model.FloatProperty()
        created = model.DateTimeProperty(auto_now=True)

        def _pre_put_hook(self):
            sum_add(self, "rating", self.article.get(), 'total_rating')
            count_inc(self, self.article.get(), 'comments_count')

        @classmethod
        def _pre_delete_hook(cls, key):
            instance = key.get()
            sum_sub(instance, "rating", instance.article.get(), 'total_rating')
            count_dec(instance, instance.article.get(), 'comments_count')

The only restriction is that each Comment modification (put or delete) into datastore should be made within transaction
with cross-group transactions flag enabled like this::

    ndb.transaction(comment.put, xg=True)


