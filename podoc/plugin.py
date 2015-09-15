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
# Plugin system
#------------------------------------------------------------------------------

class IPluginRegistry(type):
    plugins = []

    def __init__(cls, name, bases, attrs):
        if name != 'IPlugin':
            IPluginRegistry.plugins.append(cls)


class IPlugin(object):
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
