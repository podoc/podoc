# -*- coding: utf-8 -*-

"""Core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
import os.path as op

from .plugin import get_plugin

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# Utility functions
#------------------------------------------------------------------------------

def open_text(path):
    with open(path, 'r') as f:
        return f.read()


def save_text(path, contents):
    with open(path, 'w') as f:
        return f.write(contents)


#------------------------------------------------------------------------------
# Main class
#------------------------------------------------------------------------------

class Podoc(object):
    """Conversion pipeline for markup documents.

    This class implements the core conversion functionality of podoc.

    """
    opener = None
    prefilters = None
    reader = None
    filters = None
    writer = None
    postfilters = None
    saver = None

    def __init__(self):
        if self.opener is None:
            self.opener = open_text
        if self.saver is None:
            self.saver = save_text
        if self.prefilters is None:
            self.prefilters = []
        if self.filters is None:
            self.filters = []
        if self.postfilters is None:
            self.postfilters = []

    # Individual stages
    # -------------------------------------------------------------------------

    def open(self, path):
        """Open a file and return an object."""
        assert self.opener is not None
        return self.opener(path)

    def save(self, path, contents):
        """Save contents to a file."""
        assert self.saver is not None
        return self.saver(path, contents)

    def prefilter(self, contents):
        """Apply prefilters to contents."""
        for p in self.prefilters:
            contents = p(contents)
        return contents

    def read(self, contents):
        """Read contents to an AST."""
        if self.reader is None:
            raise RuntimeError("No reader has been set.")
        assert self.reader is not None
        ast = self.reader(contents)
        return ast

    def filter(self, ast):
        """Apply filters to an AST."""
        for f in self.filters:
            ast = f(ast)
        return ast

    def write(self, ast):
        """Write an AST to contents."""
        if self.writer is None:
            raise RuntimeError("No writer has been set.")
        assert self.writer is not None
        converted = self.writer(ast)
        return converted

    def postfilter(self, contents):
        """Apply postfilters to contents."""
        for p in self.postfilters:
            contents = p(contents)
        return contents

    # Partial conversion methods
    # -------------------------------------------------------------------------

    def read_contents(self, contents):
        """Read contents and return an AST.

        Prefilters -> Reader.

        """
        contents = self.prefilter(contents)
        ast = self.read(contents)
        return ast

    def read_file(self, from_path):
        """Read a file and return an AST.

        Opener -> Prefilters -> Reader.

        """
        contents = self.open(from_path)
        return self.read_contents(contents)

    def write_contents(self, ast):
        """Write an AST to contents.

        Writer -> Postfilters.

        """
        converted = self.write(ast)
        converted = self.postfilter(converted)
        return converted

    def write_file(self, to_path, ast):
        """Write an AST to a file.

        Writer -> Postfilters -> Saver.

        """
        converted = self.write_contents(ast)
        return self.save(to_path, converted) if to_path else converted

    # Complete conversion methods
    # -------------------------------------------------------------------------

    def convert_file(self, from_path, to_path=None):
        """Convert a file."""
        contents = self.open(from_path)
        converted = self.convert_contents(contents)
        return self.save(to_path, converted) if to_path else converted

    def convert_contents(self, contents):
        """Convert contents without writing files."""
        ast = self.read_contents(contents)
        ast = self.filter(ast)
        converted = self.write_contents(ast)
        return converted

    # Pipeline configuration
    # -------------------------------------------------------------------------

    def set_opener(self, func):
        """An Opener is a function `str (path)` -> `str (or object)`.

        The output may be a string or another type of object, like a file
        handle, etc.

        """
        self.opener = func
        return self

    def add_prefilters(self, funcs):
        self.prefilters.extend(funcs)
        return self

    def set_reader(self, func):
        """A reader is a function `str (or object)` -> `ast`.

        The input corresponds to the output of the file opener.

        """
        self.reader = func
        return self

    def add_filters(self, funcs):
        self.filters.extend(funcs)
        return self

    def set_writer(self, func):
        """A reader is a function `ast` -> `str (or object)`.

        The output corresponds to the input of the file saver.

        """
        self.writer = func
        return self

    def add_postfilters(self, funcs):
        self.postfilters.extend(funcs)
        return self

    def set_saver(self, func):
        """A Saver is a function `str (path), str (or object) -> None`.

        The second input corresponds to the output of the writer.

        """
        self.saver = func
        return self


#------------------------------------------------------------------------------
# Misc functions
#------------------------------------------------------------------------------

def open_file(path, plugin_name=None):
    """Open a file using a given plugin.

    If no plugin is specified, the file extension is used to find the
    appropriate plugin.

    """
    if plugin_name is None:
        search = op.splitext(path)[1]
    else:
        search = plugin_name
    plugin = get_plugin(search)()
    assert plugin
    return plugin.attach_pre(Podoc()).open(path)
