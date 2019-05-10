#!/usr/bin/env python
from setuptools import setup

with open('README.md', 'r') as f:
      long_description = f.read()

setup(name='Hydras',
      version='1.0.0',
      description='A module for constructions of structured binary packets.',
      author='Gilad Naaman',
      author_email='gilad@naaman.io',
      tests_require=["pytest"],
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/Gilnaa/Hydras",
      packages=['hydras'],
      classifiers=[
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
      ])
