# -*- coding: utf-8 -*-

"""Utility functions."""

import os.path as op

from six import string_types


#------------------------------------------------------------------------------
# Bunch
#------------------------------------------------------------------------------

class Bunch(dict):
    """A dict with additional dot syntax."""
    def __init__(self, *args, **kwargs):
        super(Bunch, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def copy(self):
        return Bunch(super(Bunch, self).copy())


#------------------------------------------------------------------------------
# File I/O
#------------------------------------------------------------------------------

def open_text(path):
    assert op.exists(path)
    with open(path, 'r') as f:
        return f.read()


def save_text(path, contents):
    with open(path, 'w') as f:
        return f.write(contents)


#------------------------------------------------------------------------------
# Path
#------------------------------------------------------------------------------

def _normalize_path(path):
    assert isinstance(path, string_types)
    assert path
    path = op.realpath(op.expanduser(path))
    return path


class Path(object):
    def __init__(self, path):
        self.path = _normalize_path(path)

    def __repr__(self):
        return '<Path `{}`>'.format(self.path)

    def exists(self):
        return op.exists(self.path)


#------------------------------------------------------------------------------
# pandoc wrapper
#------------------------------------------------------------------------------

def pandoc(from_path, to_path, **kwargs):
    """Convert a document with pandoc."""
    import pypandoc
    return pypandoc.convert(from_path, to_path, **kwargs)
