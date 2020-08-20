#!/usr/bin/env python
from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(name='Hydras',
      version='3.1.2',
      description='A module for constructions of structured binary packets.',
      author='Gilad Naaman',
      author_email='gilad@naaman.io',
      tests_require=["pytest"],
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/Gilnaa/Hydras",
      packages=find_packages(),
      classifiers=[
          'Programming Language :: Python :: 3',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
      ], install_requires=['pyelftools'],
      entry_points={
          'console_scripts': [
              'd2h = hydras.tools.dwarf2hydra:main'
          ]
      })
