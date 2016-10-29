#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='recent',
    version='0.1.1',

    description='log bash history to an sqlite database',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/trengrj/recent',

    # Author details
    author='John Trengrove',
    author_email='john@retrofilter.com',

    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[

        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Topic :: System :: Logging',
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='logging bash history database',

    py_modules=["recent"],

    entry_points={
        'console_scripts': [
            'log-recent=recent:log',
            'recent=recent:main',
        ],
    },
)
