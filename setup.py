#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from distutils.core import setup, Command
import wptablefinder

# class TestCommand(Command):
#     description = "Runs unittests."
#     user_options = []
#     def initialize_options(self):
#         pass
#     def finalize_options(self):
#         pass
#     def run(self):
#         os.system('python wptablefinder.py')

setup(
    name='wptablefinder',
    version=wptablefinder.__version__,
    description='Finds and extracts tables from Wikipedia.',
    author='Chris Spencer',
    author_email='chrisspen@gmail.com',
    url='https://github.com/chrisspen/wptablefinder',
    license='MIT',
    py_modules=['wptablefinder'],
    #https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires = [
        'fake_useragent>=0.0.8',
        'beautifulsoup4>=4.4.0',
        'lxml>=3.4.4',
        #'cssselect>=0.9.1',
        'python-dateutil>=2.4.2',
    ],
    platforms=['OS Independent'],
#    test_suite='dtree',
#     cmdclass={
#         'test': TestCommand,
#     },
)
