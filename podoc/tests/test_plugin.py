# -*- coding: utf-8 -*-

"""Test plugin system."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from ..core import save_text
from ..plugin import (IPluginRegistry, IPlugin, discover_plugins, get_plugin,
                      iter_plugins_dirs, iter_plugin_test_files)

from pytest import yield_fixture, raises


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


def test_iter_plugin_test_files():
    for plugin_dir in iter_plugins_dirs():
        if 'json' in plugin_dir:
            assert 'hello.json' in map(op.basename,
                                       iter_plugin_test_files(plugin_dir))
