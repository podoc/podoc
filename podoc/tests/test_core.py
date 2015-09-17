# -*- coding: utf-8 -*-

"""Test core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

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
    podoc.set_file_opener(lambda path: (path + ' open'))
    podoc.add_preprocessor(lambda x: x[0].upper() + x[1:])
    podoc.set_reader(lambda x: x.split(' '))
    podoc.add_filter(lambda x: (x + ['filter']))
    podoc.set_writer(lambda x: ' '.join(x))
    podoc.add_postprocessor(lambda x: x[:-1] + x[-1].upper())
    podoc.set_file_saver(lambda path, contents: (contents + ' in ' + path))

    path = 'abc'
    contents = path + ' open'
    ast = ['Abc', 'open']

    assert podoc.convert_file(path, 'path') == 'Abc open filteR in path'
    assert podoc.convert_contents(contents) == 'Abc open filteR'

    assert podoc.read_file(path) == ast
    assert podoc.read_contents(contents) == ast

    assert podoc.write_contents(ast) == 'Abc opeN'
    assert podoc.write_file('path', ast) == 'Abc opeN in path'


def test_podoc_plugins(podoc):

    class MyPlugin1(IPlugin):
        def register(self, podoc):
            podoc.set_file_opener(lambda path: (path + ' open'))
            podoc.add_preprocessor(lambda x: x[0].upper() + x[1:])

    class MyPlugin2(IPlugin):
        def register(self, podoc):
            podoc.add_postprocessor(lambda x: x[:-1] + x[-1].upper())
            podoc.set_file_saver(lambda path, contents: (contents +
                                                         ' in ' +
                                                         path))

    class MyPluginFrom(IPlugin):
        def register_from(self, podoc):
            podoc.set_reader(lambda x: x.split(' '))
            podoc.add_filter(lambda x: (x + ['filter']))

    class MyPluginTo(IPlugin):
        def register_to(self, podoc):
            podoc.set_writer(lambda x: ' '.join(x))

    plugins = (MyPlugin1, MyPlugin2)
    plugins_from = (MyPluginFrom,)
    plugins_to = (MyPluginTo,)
    podoc.set_plugins(plugins, plugins_from, plugins_to)

    contents = 'abc'
    assert podoc.convert_contents(contents) == 'Abc filteR'
    assert podoc.convert_file(contents, 'path') == 'Abc open filteR in path'


def test_open_file(hello_pandoc_path):
    with open_file(hello_pandoc_path) as f:
        assert f.name.endswith('.json')
    with open_file(hello_pandoc_path, plugin_name='json') as f:
        assert f.name.endswith('.json')
