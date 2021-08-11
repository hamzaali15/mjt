from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in mjt/__init__.py
from mjt import __version__ as version

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
