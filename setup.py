#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import re, os
from tt import __version__
from tt import __author__
from tt import __email__

CONSOLE_SCRIPTS = ['tt=tt.tt:main']

#requirements
def requirements():
    with open('requirements.txt','r',encoding = 'utf-8') as f:
        lines = f.readlines()
        return [line.replace('==','>=').strip() for line in lines]
REQUIREMENTS = requirements()

#readme
with open('README.md', 'r', encoding = 'utf-8') as f:
    README = '\n'.join(f.readlines())

#setup
setup(
    name='tt',
    version=__version__,
    description='Useful command line tools for Anuko Time Tracker',
    long_description_content_type='text/markdown',
    long_description=README,
    author=__author__,
    author_email=__email__,
    url='https://github.com/Whenti/tt',
    packages = ['tt'],
    package_dir={'tt':'tt'},
    include_package_data=True,
    install_requires=REQUIREMENTS,
    license='Apache License',
    zip_safe=False,
    keywords='command line anuko time tracker',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': CONSOLE_SCRIPTS,
    },
)