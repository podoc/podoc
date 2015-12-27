# -*- coding: utf-8 -*-

"""Test plugin system."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from ..core import save_text
from ..plugin import (IPluginRegistry, IPlugin, discover_plugins, get_plugin,
                      iter_plugins_dirs, _load_all_native_plugins)
from ..testing import _test_readers, _test_writers

from pytest import yield_fixture, raises, mark


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

@yield_fixture
def no_native_plugins():
    # Save the plugins.
    plugins = IPluginRegistry.plugins
    IPluginRegistry.plugins = []
    yield
    IPluginRegistry.plugins = plugins


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_plugin_registration(no_native_plugins):
    class MyPlugin(IPlugin):
        pass

    assert IPluginRegistry.plugins == [(MyPlugin, ())]


def test_get_plugin():
    assert get_plugin('jso').__name__ == 'JSON'
    assert get_plugin('JSO').__name__ == 'JSON'
    assert get_plugin('JSON').__name__ == 'JSON'
    assert get_plugin('json').__name__ == 'JSON'
    assert get_plugin('.json').__name__ == 'JSON'

    with raises(ValueError):
        assert get_plugin('.jso') is None
    with raises(ValueError):
        assert get_plugin('jsonn') is None


def test_discover_plugins(tempdir, no_native_plugins):
    path = op.join(tempdir, 'my_plugin.py')
    contents = '''from podoc import IPlugin\nclass MyPlugin(IPlugin): pass'''
    save_text(path, contents)
    plugins = discover_plugins([tempdir])
    assert plugins
    assert plugins[0][0].__name__ == 'MyPlugin'


def test_iter_plugins_dirs():
    assert 'json' in [op.basename(plugin_dir)
                      for plugin_dir in iter_plugins_dirs()]


def test_load_all_native_plugins(no_native_plugins):
    _load_all_native_plugins()


#------------------------------------------------------------------------------
# Test all plugins on all test files
#------------------------------------------------------------------------------

def test_reader_plugins(test_file_tuple):
    """This test is called on all plugin test files.

    It tests the readers of all plugins.

    """
    _test_readers(*test_file_tuple)


def test_writer_plugins(test_file_tuple):
    """This test is called on all plugin test files.

    It tests the writers of all plugins.

    """
    _test_writers(*test_file_tuple)


@mark.parametrize('plugin_path', iter_plugins_dirs())
def test_saver_plugins(tempdir, podoc, hello_ast, plugin_path):
    """For every plugin, save the hello AST to a file, read it, and compare
    to the original AST."""
    plugin_name = op.basename(plugin_path)
    p = get_plugin(plugin_name)()
    output_path = op.join(tempdir, 'output')
    p.attach_post(podoc).write_file(output_path, hello_ast)
    ast = p.attach_pre(podoc).read_file(output_path)
    assert ast == hello_ast
