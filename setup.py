#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="integrations-testing-framework",
    version="0.1.0",
    description="",
    author="y42",
    py_modules=["integrations_testing_framework"],
    install_requires=[
        # NB: Pin these to a more specific version for tap reliability
        "requests>=2.20.0",
        "responses==0.4.0",
    ],
    packages=find_packages(),
    classifiers=[
        "Development Status :: 1 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="integrations testing framework",
)
