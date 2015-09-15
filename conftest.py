# -*- coding: utf-8 -*-

"""py.test utilities."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from podoc import add_default_handler

from pytest import yield_fixture
from tempfile import TemporaryDirectory


#------------------------------------------------------------------------------
# Common fixtures
#------------------------------------------------------------------------------

add_default_handler('DEBUG')


@yield_fixture
def tempdir():
    with TemporaryDirectory() as tempdir:
        yield tempdir
