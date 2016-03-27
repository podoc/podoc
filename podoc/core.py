# -*- coding: utf-8 -*-

"""Core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from collections import defaultdict
import glob
import logging
import os.path as op

from six import string_types

from .utils import Bunch, load_text, dump_text
from .plugin import get_plugins

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Graph routines
#------------------------------------------------------------------------------

def _graph_from_edges(edges):
    """Return the adjacency list of a graph defined by a list of edges."""
    g = defaultdict(set)
    for a, b in edges:
        g[a].add(b)
        g[b].add(a)
    return g


def _bfs_paths(graph, start, target):
    """Generate paths from start to target."""
    # http://eddmann.com/posts/depth-first-search-and-breadth-first-search-in-python/  # noqa
    queue = [(start, [start])]
    while queue:
        (vertex, path) = queue.pop(0)
        for next in graph[vertex] - set(path):
            if next == target:
                yield path + [next]
            else:
                queue.append((next, path + [next]))


def _find_path(edges, start, target):
    """Return a shortest path in a graph defined by a list of edges."""
    graph = _graph_from_edges(edges)
    try:
        return next(_bfs_paths(graph, start, target))
    except StopIteration:
        return None


#------------------------------------------------------------------------------
# Main class
#------------------------------------------------------------------------------

def _get_annotation(func, name):
    return getattr(func, '__annotations__', {}).get(name, None)


class Podoc(object):
    """Conversion pipeline for markup documents.

    This class implements the core conversion functionality of podoc.

    Parameters
    ----------

    plugins : list of str (None)
        List of plugins to load. By default, load all plugins found.
    with_pandoc : bool (True)
        Whether to load all pandoc conversion paths.

    """

    def __init__(self, plugins=None, with_pandoc=True):
        self._funcs = {}  # mapping `(lang0, lang1) => func`
        self._langs = {}  # mapping `lang: Bunch()`
        self._load_plugins(plugins, with_pandoc)

    def _load_plugins(self, plugins=None, with_pandoc=True):
        """Load plugins. By default (None), all plugins found are loaded."""
        # Load plugins.
        plugins = plugins if plugins is not None else get_plugins()
        for p in plugins:
            # Skip pandoc plugin.
            if not with_pandoc and p.__name__ == 'PandocPlugin':
                continue
            p().attach(self)

    # Main methods
    # -------------------------------------------------------------------------

    def register_func(self, func=None, source=None, target=None):
        """Register a conversion function between two languages."""
        if func is None:
            return lambda _: self.register_func(_, source=source,
                                                target=target)
        assert func
        source = source or _get_annotation(func, 'source')
        target = target or _get_annotation(func, 'target')
        assert source
        assert target
        if (source, target) in self._funcs:
            logger.debug("Conversion `%s -> %s` already registered, skipping.",
                         source, target)
            return
        logger.log(5, "Register conversion `%s -> %s`.", source, target)
        self._funcs[(source, target)] = func

    def register_lang(self, name, file_ext=None,
                      load_func=None, dump_func=None,
                      loads_func=None, dumps_func=None,
                      **kwargs):
        """Register a language with a file extension and load/dump
        functions."""
        if file_ext:
            assert file_ext.startswith('.')
        if name in self._langs:
            logger.log(5, "Language `%s` already registered, skipping.", name)
            return
        logger.log(5, "Register language `%s`.", name)
        self._langs[name] = Bunch(file_ext=file_ext,
                                  load_func=load_func or load_text,
                                  dump_func=dump_func or dump_text,
                                  loads_func=loads_func or (lambda _: _),
                                  dumps_func=dumps_func or (lambda _: _),
                                  **kwargs)

    def convert(self, obj_or_path, source=None, target=None,
                lang_list=None, output=None):
        """Convert an object by passing it through a chain of conversion
        functions."""
        obj = obj_or_path
        # NOTE: 'json' is an alias for 'ast', to match with pandoc's
        # terminology.
        source = source if source != 'json' else 'ast'
        target = target if target != 'json' else 'ast'
        # If the output is specified and not the target, infer the target
        # from the file extension.
        if target is None and output is not None:
            target = self.get_lang_for_file_ext(op.splitext(output)[1])
        # NOTE: decide whether the object is a path or contents string.
        if (isinstance(obj_or_path, string_types) and
                len(obj_or_path) <= 1024 and  # this is to avoid passing huge
                                              # strings to op.exists(), which
                                              # crashes sometimes.
                op.exists(obj_or_path)):
            # Convert a file to a target format.
            path = obj_or_path
            assert target
            # Get the source from the file extension
            if source is None and lang_list is None:
                source = self.get_lang_for_file_ext(op.splitext(path)[1])
            assert source
            # Load the object.
            obj = self.load(path, source)
        # At this point, we should have a non-empty object.
        assert obj
        if lang_list is None:
            # Find the shortest path from source to target in the conversion
            # graph.
            assert source and target
            lang_list = _find_path(self.conversion_pairs,
                                   source, target)
            if not lang_list:
                raise ValueError("No path found from `{}` to `{}`.".format(
                                 source, target))
        assert isinstance(lang_list, (tuple, list))
        # Iterate over all successive pairs.
        for t0, t1 in zip(lang_list, lang_list[1:]):
            # Get the function registered for t0, t1.
            f = self._funcs.get((t0, t1), None)
            if not f:
                raise ValueError("No function registered for `{}` => `{}`.".
                                 format(t0, t1))
            # Perform the conversion.
            obj = f(obj)
        if output:
            self.dump(obj, output, lang=target)
        return obj

    # Properties
    # -------------------------------------------------------------------------

    @property
    def languages(self):
        """List of all registered languages."""
        return sorted(self._langs)

    @property
    def conversion_pairs(self):
        """List of registered conversion pairs."""
        return sorted(self._funcs.keys())

    # File-related methods
    # -------------------------------------------------------------------------

    def get_files_in_dir(self, path, lang=None):
        """Return the list of files of a given language in a directory."""
        assert path
        path = op.realpath(op.expanduser(path))
        assert op.exists(path)
        assert op.isdir(path)
        # Find the file extension for the given language.
        file_ext = (self._langs[lang].file_ext or '') if lang else ''
        filenames = glob.glob(op.join(path, '*' + file_ext))
        return [op.join(path, fn) for fn in filenames]

    def get_lang_for_file_ext(self, file_ext):
        """Get the language registered with a given file extension."""
        for name, b in self._langs.items():
            if b.file_ext == file_ext:
                return name
        raise ValueError(("The file extension `{}` hasn't been "
                          "registered.").format(file_ext))

    def get_file_ext(self, lang):
        """Return the file extension registered for a given language."""
        return self._langs[lang].file_ext

    def load(self, path, lang=None):
        """Load a file which has a registered file extension."""
        # Find the language corresponding to the file's extension.
        file_ext = op.splitext(path)[1]
        lang = lang or self.get_lang_for_file_ext(file_ext)
        # Load the file using the function registered for the language.
        return self._langs[lang].load_func(path)

    def dump(self, contents, path, lang=None):
        """Dump an object to a file."""
        # Find the language corresponding to the file's extension.
        file_ext = op.splitext(path)[1]
        lang = lang or self.get_lang_for_file_ext(file_ext)
        # Dump the file using the function registered for the language.
        return self._langs[lang].dump_func(contents, path)

    def loads(self, s, lang=None):
        """Load an object from its string representation."""
        assert lang
        # Load the string using the function registered for the language.
        return self._langs[lang].loads_func(s)

    def dumps(self, contents, lang=None):
        """Dump an object to a string."""
        assert lang
        # Dump the string using the function registered for the language.
        return self._langs[lang].dumps_func(contents)
