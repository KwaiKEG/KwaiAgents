#!/usr/bin/env python
import io
from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('requirements.txt') as f:
    requirements = f.read()

setup(
    # Metadata
    name='kwaiagents',
    version='0.0.1',
    python_requires='>=2.7,>=3.6',
    author='Haojie Pan',
    author_email='panhaojie@kuaishou.com',
    description='Kwaiagents',
    long_description=readme,
    long_description_content_type='text/markdown',
    entry_points = {
        'console_scripts': [
            'kagentsys=kwaiagents.agent_start:main']
    },
    packages=find_packages(),
    license='Attribution-NonCommercial-ShareAlike 4.0',

    # Package info
    install_requires=requirements
)
