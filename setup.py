#!/usr/bin/env python
from setuptools import setup

setup(
    name="integrations-testing-framework",
    version="0.1.0",
    description="",
    author="y42",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["integrations_testing_framework"],
    install_requires=[
        # NB: Pin these to a more specific version for tap reliability
        "requests==2.26.0",
        "responses==0.17.0",
    ],
    packages=["integrations_testing_framework"],
)
