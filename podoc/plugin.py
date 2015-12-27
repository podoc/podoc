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
            plugin_tuple = (cls, cls.file_extensions)
            if plugin_tuple not in IPluginRegistry.plugins:
                IPluginRegistry.plugins.append(plugin_tuple)


class IPlugin(object, metaclass=IPluginRegistry):
    file_extensions = ()

    def attach(self, podoc, steps):
        """Attach the plugin to the podoc.

        By default, call `self.set_<step>(podoc)` for all specified steps.

        May be overridden by the plugin.

        """
        for step in steps:
            getattr(self, 'set_' + step)(podoc)

    def get_opener(self):
        pass

    def get_filters(self):
        return []

    def get_reader(self):
        pass

    def get_prefilters(self):
        return []

    def get_writer(self):
        pass

    def get_postfilters(self):
        return []

    def get_saver(self):
        pass

    def set_opener(self, podoc):
        """Attach `self.opener` to the podoc.

        May be overridden by the plugin.

        """
        if hasattr(self, 'opener'):
            podoc.set_opener(self.opener)

    def set_prefilters(self, podoc):
        """Attach `self.prefilter` to the podoc.

        May be overridden by the plugin.

        """
        if hasattr(self, 'prefilter'):
            podoc.add_prefilter(self.prefilter)

    def set_reader(self, podoc):
        """Attach `self.reader` to the podoc.

        May be overridden by the plugin.

        """
        if hasattr(self, 'reader'):
            if podoc.reader:
                raise RuntimeError("A reader has already been attached.")
            podoc.set_reader(self.reader)

    def set_filters(self, podoc):
        """Attach `self.filter` to the podoc.

        May be overridden by the plugin.

        """
        if hasattr(self, 'filter'):
            podoc.add_filter(self.filter)

    def set_writer(self, podoc):
        """Attach `self.writer` to the podoc.

        May be overridden by the plugin.

        """
        if hasattr(self, 'writer'):
            if podoc.writer:
                raise RuntimeError("A writer has already been attached.")
            podoc.set_writer(self.writer)

    def set_postfilters(self, podoc):
        """Attach `self.postfilter` to the podoc.

        May be overridden by the plugin.

        """
        if hasattr(self, 'postfilter'):
            podoc.add_postfilter(self.postfilter)

    def set_saver(self, podoc):
        """Attach `self.saver` to the podoc.

        May be overridden by the plugin.

        """
        if hasattr(self, 'saver'):
            podoc.set_saver(self.saver)


def get_plugin(name_or_ext):
    """Get a plugin class from its name or file extension."""
    name_or_ext = name_or_ext.lower()
    for (plugin, file_extension) in IPluginRegistry.plugins:
        if (name_or_ext in plugin.__name__.lower() or
                name_or_ext in file_extension):
            return plugin
    raise ValueError("The plugin %s cannot be found." % name_or_ext)


def attach_plugin(plugin_name, podoc, steps):
    plugin = get_plugin(plugin_name)
    podoc.set_opener(plugin.get_opener())
    for f in plugin.get_prefilters():
        podoc.add_prefilter(f)
    podoc.set_reader(plugin.get_reader())
    for f in plugin.get_filters():
        podoc.add_filter(f)
    podoc.set_writer(plugin.get_writer())
    for f in plugin.get_postfilters():
        podoc.add_postfilter(f)
    podoc.set_saver(plugin.get_saver())


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


def _load_all_native_plugins():
    """Load all native plugins when importing the library."""
    curdir = op.dirname(op.realpath(__file__))
    plugins_dir = op.join(curdir, 'plugins')
    discover_plugins([plugins_dir])
