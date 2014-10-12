#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='thingiverse',
    version='0.0.1',
    description='Python Thingiverse API wrapper',
    long_description=''.join(open('README.rst').readlines()),
    keywords='thingiverse, 3D, API, 3D printing',
    author='Erin RobotGrrl',
    author_email='erin@robotgrrl.com',
    maintainer='Miro Hrončok',
    maintainer_email='miro@hroncok.cz',
    install_requires=['rauth', 'requests'],
    license='MIT',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Multimedia :: Graphics :: 3D Modeling',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
    ]
)
