# -*- coding: utf-8 -*-

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from pytest import raises

from ..core import open_text, save_text, open_file
from ..plugin import IPlugin


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_open_save_text(tempdir, hello_markdown):
    path = op.join(tempdir, 'test.txt')

    save_text(path, hello_markdown)
    assert open_text(path) == hello_markdown


def test_podoc_complete(podoc):
    path = 'abc'
    contents = path + ' open'
    ast = ['Abc', 'open']

    with raises(RuntimeError):
        podoc.read_contents(contents)
    with raises(RuntimeError):
        podoc.write_contents(ast)

    podoc.set_opener(lambda path: (path + ' open'))
    podoc.add_prefilters([lambda x: x[0].upper() + x[1:]])
    podoc.set_reader(lambda x: x.split(' '))
    podoc.add_filters([lambda x: (x + ['filter'])])
    podoc.set_writer(lambda x: ' '.join(x))
    podoc.add_postfilters([lambda x: x[:-1] + x[-1].upper()])
    podoc.set_saver(lambda path, contents: (contents + ' in ' + path))

    assert podoc.convert_file(path, 'path') == 'Abc open filteR in path'
    assert podoc.convert_contents(contents) == 'Abc open filteR'

    assert podoc.read_file(path) == ast
    assert podoc.read_contents(contents) == ast

    assert podoc.write_contents(ast) == 'Abc opeN'
    assert podoc.write_file('path', ast) == 'Abc opeN in path'


def test_podoc_errors(podoc):
    class EmptyPlugin0(IPlugin):
        pass

    class EmptyPluginFilter(IPlugin):
        pass

    class EmptyPluginFrom(IPlugin):
        def reader(self, contents):
            pass

    class EmptyPluginTo(IPlugin):
        def writer(self, ast):
            pass

    EmptyPlugin0().attach(podoc)

    # Only one reader can be attached.
    EmptyPluginFrom().attach(podoc)
    with raises(RuntimeError):
        EmptyPluginFrom().attach(podoc)

    # Only one writer can be attached.
    EmptyPluginTo().attach(podoc)
    with raises(RuntimeError):
        EmptyPluginTo().attach(podoc)

    # Several filters can be attached.
    EmptyPluginFilter().attach(podoc)
    EmptyPluginFilter().attach(podoc)


def test_podoc_plugins(podoc):

    class MyPlugin1(IPlugin):
        def opener(self, path):
            return path + ' open'

        def prefilter(self, contents):
            return contents[0].upper() + contents[1:]

    class MyPlugin2(IPlugin):
        def postfilter(self, contents):
            return contents[:-1] + contents[-1].upper()

        def saver(self, path, contents):
            return contents + ' in ' + path

    class MyPluginFrom(IPlugin):
        def reader(self, contents):
            return contents.split(' ')

        def filter(self, ast):
            return ast + ['filter']

    class MyPluginTo(IPlugin):
        def writer(self, ast):
            return ' '.join(ast)

    MyPlugin1().attach(podoc)
    MyPlugin2().attach(podoc)
    MyPluginFrom().attach(podoc)
    MyPluginTo().attach(podoc)

    contents = 'abc'
    assert podoc.convert_contents(contents) == 'Abc filteR'
    assert podoc.convert_file(contents, 'path') == 'Abc open filteR in path'


def test_open_file(hello_json_path):
    for d in (open_file(hello_json_path),
              open_file(hello_json_path, plugin_name='json')):
        assert len(d) == 2
        assert 'unMeta' in d[0]
        assert isinstance(d[1], list)
