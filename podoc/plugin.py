# -*- coding: utf-8 -*-

"""Plugin system.

Code from http://eli.thegreenplace.net/2012/08/07/fundamental-concepts-of-plugin-infrastructures  # noqa

"""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import imp
import logging
import os
import os.path as op

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# IPlugin interface
#------------------------------------------------------------------------------

class IPluginRegistry(type):
    plugins = []

    def __init__(cls, name, bases, attrs):
        if name != 'IPlugin':
            IPluginRegistry.plugins.append(cls)


class IPlugin(object, metaclass=IPluginRegistry):
    format_name = None
    file_extensions = ()

    def register(self, podoc):
        """Called when the plugin is activated with `--plugins`."""
        pass

    def register_from(self, podoc):
        """Called when the plugin is activated with `--from`."""
        pass

    def register_to(self, podoc):
        """Called when the plugin is activated with `--to`."""
        pass


#------------------------------------------------------------------------------
# Plugins discovery
#------------------------------------------------------------------------------

def discover_plugins(dirs):
    """Discover the plugin classes contained in Python files.

    Parameters
    ----------

    dirs : list
        List of directory names to scan.

    Returns
    -------

    plugins : list
        List of plugin classes.

    """
    for dir in dirs:
        for filename in os.listdir(dir):
            modname, ext = op.splitext(filename)
            if ext == '.py':
                file, path, descr = imp.find_module(modname, [dir])
                if file:
                    # Loading the module registers the plugin in
                    # IPluginRegistry
                    mod = imp.load_module(modname, file, path, descr)  # noqa
    return IPluginRegistry.plugins


def iter_plugins_dirs():
    """Iterate over all plugin directories."""
    curdir = op.dirname(op.realpath(__file__))
    plugins_dir = op.join(curdir, 'plugins')
    # TODO: add other plugin directories (user plugins etc.)
    names = [name for name in sorted(os.listdir(plugins_dir))
             if not name.startswith(('.', '_')) and
             op.isdir(op.join(plugins_dir, name))]

    for name in names:
        yield op.join(plugins_dir, name)


def iter_plugin_test_files(plugin_dir):
    """Iterate over all test_file files in a plugin directory."""
    test_files_path = op.join(plugin_dir, 'test_files')
    test_files = (os.listdir(test_files_path)
                  if op.exists(test_files_path) else [])
    for filename in test_files:
        yield filename
