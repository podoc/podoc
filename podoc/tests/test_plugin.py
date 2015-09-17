# -*- coding: utf-8 -*-

"""Test plugin system."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os.path as op

from ..core import save_text
from ..plugin import (IPluginRegistry, IPlugin, discover_plugins,
                      iter_plugins_dirs)


#------------------------------------------------------------------------------
# Fixtures
#------------------------------------------------------------------------------

def setup():
    IPluginRegistry.plugins = []


def teardown():
    IPluginRegistry.plugins = []


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------

def test_plugin_registration():
    class MyPlugin(IPlugin):
        pass

    assert IPluginRegistry.plugins == [MyPlugin]


def test_discover_plugins(tempdir):
    path = op.join(tempdir, 'my_plugin.py')
    contents = '''from podoc import IPlugin\nclass MyPlugin(IPlugin): pass'''
    save_text(path, contents)
    plugins = discover_plugins([tempdir])
    assert plugins
    assert plugins[0].__name__ == 'MyPlugin'


def test_iter_plugins_dirs():
    assert 'json' in [op.basename(plugin_dir)
                      for plugin_dir in iter_plugins_dirs()]
