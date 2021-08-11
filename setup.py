# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import re
from ast import literal_eval


with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in mjt/__init__.py
from mjt import __version__ as version
_version_re = re.compile(f'__version__\s+=\s+(.*)')

with open('mjt/__init__.py', 'rb') as f:
	version = str(literal_eval(_version_re.search(f.read().decode('utf-8')).group(1)))
	
setup(
	name='mjt',
	version=version,
	description='MJT',
	author='RF',
	author_email='hamza@rf.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
