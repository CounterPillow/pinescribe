#!/usr/bin/env python3
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='pinescribe',
    version='0.1',
    description='A tool for flashing the PineNote',

    entry_points={
        'console_scripts': [
            'pinescribe=pinescribe:main',
        ],
    },

    install_requires=[
        'libusb1',
        'click',
    ]
)
