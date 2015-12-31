# -*- coding: utf-8 -*-

"""Utility functions."""

import logging
import os.path as op

from six import string_types

logger = logging.getLogger(__name__)


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

def pandoc(obj, to, **kwargs):
    """Convert a string or a file with pandoc."""
    import pypandoc
    return pypandoc.convert(obj, to, **kwargs)


def has_pandoc():  # pragma: no cover
    try:
        import pypandoc
        pypandoc.get_pandoc_version()
        return True
    except ImportError:
        logger.debug("pypandoc is not installed.")
    except FileNotFoundError:
        logger.debug("pandoc is not installed.")
    return False
