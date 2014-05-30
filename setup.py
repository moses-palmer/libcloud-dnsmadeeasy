#!/usr/bin/env python
# coding=utf-8

import os
import setuptools
import sys

from setuptools.command.test import test


NAME = 'libcloud-dnsmadeeasy'
DESCRIPTION = 'A driver for DNSMadeEasy for libcloud DNS'
URL = 'https://github.com/moses-palmer/libcloud-dnsmadeeasy'
AUTHOR_EMAIL = 'moses.palmer@gmail.com'
SCRIPTS = []
INSTALL_REQUIRES = [
    'hammock >=0.2.4',
    'apache-libcloud >=0.14.1']
SETUP_REQUIRES = INSTALL_REQUIRES


BASE_DIR = os.path.dirname(__file__)
LIB_DIR = os.path.join(BASE_DIR, 'lib')


sys.path.append(LIB_DIR)


# Read globals from <package>._info without loading it
INFO = {}
for name in os.listdir(LIB_DIR):
    try:
        with open(os.path.join(
                LIB_DIR,
                name,
                '_info.py')) as f:
            for line in f:
                try:
                    name, value = (i.strip() for i in line.split('='))
                    if name.startswith('__') and name.endswith('__'):
                        INFO[name[2:-2]] = eval(value)
                except ValueError:
                    pass
    except IOError:
        pass


class test_runner(test):
    user_options = [
        ('suites=', 's', 'A list of test suites separated by comma (,)')]

    def initialize_options(self):
        self.suites = None

    def finalize_options(self):
        if not self.suites is None:
            self.suites = self.suites.split(',')

    def run(self):
        import importlib
        import tests

        failures = tests.run(self.suites)

        print('')
        print('All test suites completed with %d failed tests' % len(failures))
        if failures:
            sys.stderr.write('Failed tests:\n%s\n' % '\n'.join(
                '\t%s - %s' % (test.name, test.message)
                    for test in failures))
        sys.exit(len(failures))


setuptools.setup(
    name = NAME,
    description = DESCRIPTION,
    version = '.'.join(str(v) for v in INFO['version']),
    author = INFO['author'],
    author_email = AUTHOR_EMAIL,
    url = URL,

    package_dir = {'': LIB_DIR},
    packages = setuptools.find_packages(LIB_DIR,
        exclude = [
            'tests',
            'tests.suites']),

    scripts = SCRIPTS,

    install_requires = INSTALL_REQUIRES,
    setup_requires = SETUP_REQUIRES,

    zip_safe = True,

    cmdclass = {'test': test_runner})
