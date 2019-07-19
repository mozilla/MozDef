#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = [ ]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Mozilla Infosec",
    author_email='infosec-pypi@mozilla.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="IP geolocation for authentication events with MozDef ",
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='mozdef_geomodel',
    name='mozdef_geomodel',
    packages=find_packages(include=['mozdef_geomodel']),
    setup_requires=setup_requirements,
    test_suite='mozdef_geomodel',
    tests_require=test_requirements,
    url='https://github.com/mozilla/mozdef',
    version='0.1.0',
    zip_safe=False,
)
