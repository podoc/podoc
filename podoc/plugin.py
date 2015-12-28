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
            logger.debug("Register plugin %s.", name)
            if cls not in IPluginRegistry.plugins:
                IPluginRegistry.plugins.append(cls)


class IPlugin(object, metaclass=IPluginRegistry):
    def attach(self, podoc):
        pass


def get_plugin(name):
    """Get a plugin class from its name."""
    name = name.lower()
    for plugin in IPluginRegistry.plugins:
        if name in plugin.__name__.lower():
            return plugin
    raise ValueError("The plugin %s cannot be found." % name)


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
    # Scan all subdirectories recursively.
    for plugin_dir in dirs:
        # logger.debug("Scanning %s", plugin_dir)
        plugin_dir = op.realpath(plugin_dir)
        for subdir, dirs, files in os.walk(plugin_dir):
            # Skip test folders.
            base = op.basename(subdir)
            if 'test' in base or '__' in base:
                continue
            logger.debug("Scanning %s.", subdir)
            for filename in files:
                if (filename.startswith('__') or
                        not filename.endswith('.py')):
                    continue  # pragma: no cover
                logger.debug("  Found %s.", filename)
                path = os.path.join(subdir, filename)
                modname, ext = op.splitext(filename)
                file, path, descr = imp.find_module(modname, [subdir])
                if file:
                    # Loading the module registers the plugin in
                    # IPluginRegistry
                    mod = imp.load_module(modname, file, path, descr)  # noqa
    return IPluginRegistry.plugins


def _load_all_native_plugins():
    """Load all native plugins when importing the library."""
    curdir = op.dirname(op.realpath(__file__))
    # The default plugins are subfolders within podoc/podoc.
    # List of subdirs that do not start with _.
    subdirs = [d for d in os.listdir(curdir) if op.isdir(op.join(curdir, d))]
    dirs = [op.join(curdir, subdir) for subdir in subdirs
            if not subdir.startswith('_')]
    discover_plugins(dirs)
