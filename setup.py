from __future__ import unicode_literals

import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']


setup(
    name='Mopidy-RFID-Frontend',
    version=get_version('mopidy_rfid_frontend/__init__.py'),
    url='https://github.com/glogiotatidis/mopidy-rfid-frontend',
    license='Apache License, Version 2.0',
    author='Giorgos Logiotatidis',
    author_email='seadog@sealabs.net',
    description='Mopidy extension to load Albums from RFID tags',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 1.0',
        'Pykka >= 1.1',
        'mfrc522'
    ],
    dependency_links=[
        'https://github.com/glogiotatidis/MFRC522-python/archive/master.tar.gz#egg=mfrc522',
    ],
    entry_points={
        'mopidy.ext': [
            'rfid-frontend = mopidy_rfid_frontend:Extension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
