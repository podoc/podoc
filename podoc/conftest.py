# -*- coding: utf-8 -*-

"""py.test utilities."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
from tempfile import TemporaryDirectory

from pytest import yield_fixture

from podoc import add_default_handler


#------------------------------------------------------------------------------
# Common fixtures
#------------------------------------------------------------------------------

logging.getLogger().setLevel(logging.DEBUG)
add_default_handler('DEBUG')


@yield_fixture
def tempdir():
    with TemporaryDirectory() as tempdir:
        yield tempdir


# def pytest_generate_tests(metafunc):
#     """Generate the test_file_tuple fixture to test all plugin test files."""
#     if 'test_file_tuple' in metafunc.fixturenames:

#         def _name(tuple):
#             """Name of the parameterized test: <plugin>_<example_file>."""
#             return '_'.join(tuple[:2])

#         metafunc.parametrize('test_file_tuple', iter_test_files(), ids=_name)
