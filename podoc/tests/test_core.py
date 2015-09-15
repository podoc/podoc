# -*- coding: utf-8 -*-

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from pytest import yield_fixture

from ..core import Podoc, open_text, save_text


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

@yield_fixture
def podoc():
    yield Podoc()


@yield_fixture
def contents():
    contents = 'hello *world*!'
    yield contents


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_open_save_text(tempdir, contents):
    path = op.join(tempdir, 'test.txt')

    save_text(path, contents)
    assert open_text(path) == contents


def test_podoc_trivial(tempdir, podoc, contents):
    # In-memory
    assert podoc.convert_contents(contents) == contents

    # Convert from file to file
    from_path = op.join(tempdir, 'test_from.txt')
    to_path = op.join(tempdir, 'test_to.txt')
    save_text(from_path, contents)
    podoc.convert_file(from_path, to_path)
    assert open_text(to_path) == contents


def test_podoc_complete(podoc):
    podoc.set_file_opener(lambda path: (path + ' open'))
    podoc.add_preprocessor(lambda x: x[0].upper() + x[1:])
    podoc.set_reader(lambda x: x.split(' '))
    podoc.add_filter(lambda x: (x + ['filter']))
    podoc.set_writer(lambda x: ' '.join(x))
    podoc.add_postprocessor(lambda x: x[:-1] + x[-1].upper())
    podoc.set_file_saver(lambda path, contents: (contents + ' in ' + path))

    contents = 'abc'
    assert podoc.convert_contents(contents) == 'Abc filteR'

    assert podoc.convert_file(contents, 'path') == 'Abc open filteR in path'
