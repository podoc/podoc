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

from .utils import _load_test_file, _test_file_path

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


def iter_plugin_examples(plugin_dir):
    """Iterate over all example files in a plugin directory."""
    examples_path = op.join(plugin_dir, 'examples')
    examples = os.listdir(examples_path) if op.exists(examples_path) else []
    for filename in examples:
        yield filename


def iter_plugin_fixtures():
    """Generate all example fixtures from all loaded plugins."""

    def _make_fixtures(plugin_dir, example_fn):
        plugin_name = op.basename(plugin_dir)
        example_name = op.splitext(example_fn)[0]

        # Register the fixture <example>_<plugin>_path
        def fixture_path():
            yield _test_file_path(example_fn)
        fixture_path.__name__ = '{}_{}_path'.format(example_name, plugin_name)

        # Register the fixture <example>_<plugin>
        def fixture():
            yield _load_test_file(example_fn)
        fixture.__name__ = '{}_{}'.format(example_name, plugin_name)

        return (fixture_path, fixture)

    # Register fixtures of all discovered plugin example files
    for plugin_dir in iter_plugins_dirs():
        logger.debug("Discovered plugin: %s.", plugin_dir)
        for fn in iter_plugin_examples(plugin_dir):
            logger.debug("    Found file example: %s", fn)
            yield from _make_fixtures(plugin_dir, fn)


# def open_with_plugin(path, plugin):
#     """Open a file using a plugin."""
#     return Podoc().set_plugins(plugins_from=[plugin]).open(path)
