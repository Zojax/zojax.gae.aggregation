# -*- coding: utf-8 -*-
"""Setup script."""

import os
from distutils.core import setup


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

def gen_data_files(*dirs):
    results = []

    for src_dir in dirs:
        for root,dirs,files in os.walk(src_dir):
            results.append((root, map(lambda f:root + "/" + f, files)))
    return results


setup(
    name='zojax.gae.aggregation',
    version='0.1',
    author="Yaroslav D.",
    author_email='developers@zojax.com',
    description=("""Datastore ndb aggregation tool for Google App Engine (Python).
                    Makes aggregation operations like count, sum, average easier.
                    Requires Google App Engine to be installed and available in python path.
                """),
    long_description=(
        read('README.rst')
        ),
    license="Apache License 2.0",
    keywords="google app engine gae aggregation",
    classifiers=[
        'Development Status :: 5 - Development/Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
        ],
    url='',
    packages=['zojax', 'zojax.gae', 'zojax.gae.aggregation'],
    package_dir = {'': 'src'},
    #package_data={'zojax': ['zojax/gae/migration/templates/*.html']},
    #data_files = gen_data_files("src/zojax/gae/migration/templates",),
    include_package_data=True,
    namespace_packages=['zojax', 'zojax.gae'],
    install_requires=[
        'distribute',
        'webtest'
    ],
    zip_safe=False,
)
