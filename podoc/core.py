# -*- coding: utf-8 -*-

"""Core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import glob
import logging
import os.path as op

from .utils import Bunch, open_text, save_text

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Main class
#------------------------------------------------------------------------------

def _get_annotation(func, name):
    return getattr(func, '__annotations__', {}).get(name, None)


def _find_path(edges, source, target):
    """Find a path from source to target in a graph specified as a list
    of edges."""
    out = None
    if (source, target) in edges:
        # Direct conversion exists.
        out = [source, target]
    else:
        # Find an intermediate format.
        inter0 = [t1 for t0, t1 in edges if t0 == source]
        inter1 = [t0 for t0, t1 in edges if t1 == target]
        inter = sorted(set(inter0).intersection(inter1))
        if inter:
            out = [source, inter[0], target]
    return out


class Podoc(object):
    """Conversion pipeline for markup documents.

    This class implements the core conversion functionality of podoc.

    """
    def __init__(self):
        self._funcs = {}  # mapping `(lang0, lang1) => func`
        self._langs = {}  # mapping `lang: Bunch()`

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
        self._funcs[(source, target)] = func

    def register_lang(self, name, file_ext=None,
                      open_func=None, save_func=None):
        """Register a language with a file extension and open/save
        functions."""
        if file_ext:
            assert file_ext.startswith('.')
        self._langs[name] = Bunch(file_ext=file_ext,
                                  open_func=open_func or open_text,
                                  save_func=save_func or save_text,
                                  )

    def convert(self, obj, lang_list):
        """Convert an object by passing it through a chain of conversion
        functions."""
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

    def open(self, path):
        """Open a file which has a registered file extension."""
        # Find the language corresponding to the file's extension.
        file_ext = op.splitext(path)[1]
        lang = self.get_lang_for_file_ext(file_ext)
        # Open the file using the function registered for the language.
        return self._langs[lang].open_func(path)

    def save(self, path, contents):
        """Save an object to a file."""
        # Find the language corresponding to the file's extension.
        file_ext = op.splitext(path)[1]
        lang = self.get_lang_for_file_ext(file_ext)
        # Save the file using the function registered for the language.
        return self._langs[lang].save_func(path, contents)
