#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import sys
import fnmatch

# Make sure we import from working tree
pynagbase = os.path.dirname(os.path.realpath(__file__ + "/.."))
sys.path.insert(0, pynagbase)

import unittest2
import doctest
import mock  # This import is here on purpose to make it obvious if mock is not installed.

# Make sure all tests run from a fixed path, this also makes sure
# That pynag in local directory is imported before any system-wide
# installs of pynag
from tests import tests_dir

import pynag


def get_python_files():
    """Get a list of all python files inside pynag subdirectory"""
    matches = []
    os.chdir(pynagbase)
    for root, dirnames, filenames in os.walk('pynag'):
        for filename in fnmatch.filter(filenames, '*.py'):
            if filename.endswith('autogenerated_commands.py'):
                continue
            matches.append(os.path.join(root, filename))
    return matches


def get_all_pynag_modules():
    for filename in get_python_files():
        filename = filename.replace('.py', '')
        filename = filename.replace('__init__', '')
        filename = filename.replace('/', '.')
        filename = filename.strip('.')
        module_name = filename
        try:
            module = __import__(module_name, locals(), globals(), [module_name], -1)
        except:
            import importlib
            module = importlib.import_module(module_name)
        yield module


def get_all_doctests():
    flags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
    finder = doctest.DocTestFinder(exclude_empty=False)
    for module in get_all_pynag_modules():
        yield doctest.DocTestSuite(
            module,
            test_finder=finder,
            setUp=set_up_for_doc_tests,
            optionflags=flags)


def load_tests(loader=None, tests=None, pattern=None):
    """ Discover and load all unit tests in all files named ``*_test.py`` in ``./src/`` """
    suite = unittest2.TestSuite()

    # Add all doctests to our test suite:
    for doc_test in get_all_doctests():
        suite.addTest(doc_test)

    # Load unit tests from all files starting with test_*
    for all_test_suite in unittest2.defaultTestLoader.discover('.', pattern='test_*.py'):
        for test_suite in all_test_suite:
            if isinstance(test_suite, unittest2.suite.TestSuite):
                suite.addTests(test_suite)

    return suite


def set_up_for_doc_tests(test_case):
    """For doctests that require a valid config to function, we point them to dataset01."""
    os.chdir(os.path.join(tests_dir, 'dataset01'))
    pynag.Model.config = pynag.Parsers.config(cfg_file="./nagios/nagios.cfg")

if __name__ == "__main__":
    unittest2.main()

# vim: sts=4 expandtab autoindent
