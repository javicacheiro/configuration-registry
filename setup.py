#!/usr/bin/env python

from setuptools import setup

setup(
    name='configuration-registry',
    version='0.5.0',
    author='Jonatan Enes & Javier Cacheiro',
    author_email='bigdata-dev@listas.cesga.es',
    url='https://github.com/javicacheiro/configuration-registry',
    license='MIT',
    description='Python Resource Allocation API',
    long_description=open('README.rst').read(),
    py_modules=['registry'],
    install_requires=['kvstore', 'requests', 'jinja2', 'PyYAML', 'futures'],
    test_suite='tests',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
