# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), 'README.md'),
        encoding='utf-8') as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='s3-static-sync',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    description='',
    long_description=README,
    url='',
    install_requires=[
        'boto3',
        'click'
    ],
    entry_points={
        'console_scripts': [
            's3_static_sync = s3_static_sync.app:runner'
        ]
    }
)
