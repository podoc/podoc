# -*- coding: utf-8 -*-

"""Utility functions."""

from contextlib import contextmanager
import logging
import os.path as op
import sys

from six import string_types, StringIO, PY2

logger = logging.getLogger(__name__)


if PY2:
    # This exception is only defined in Python 3.
    class FileNotFoundError(OSError):  # pragma: no cover
        pass


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
        out = f.read()
    return out


def save_text(path, contents):
    with open(path, 'w') as f:
        return f.write(contents)


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


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
# Testing utils
#------------------------------------------------------------------------------

def get_test_file_path(podoc, lang, filename):
    curdir = op.realpath(op.dirname(__file__))
    file_ext = podoc.get_file_ext(lang)
    # Construct the directory name for the language and test filename.
    dirname = op.realpath(op.join(curdir, lang))
    path = op.join(dirname, 'test_files', filename + file_ext)
    assert op.exists(path)
    return path


def assert_equal(p0, p1):
    if isinstance(p0, string_types) and op.exists(p0):
        # TODO: non text files
        # NOTE: included text files have a trailing `\n`.
        assert_equal(open_text(p0), open_text(p1))
        return
    if isinstance(p0, string_types):
        assert p0.rstrip('\n') == p1.rstrip('\n')
        return
    assert p0 == p1


#------------------------------------------------------------------------------
# pandoc wrapper
#------------------------------------------------------------------------------

PANDOC_MARKDOWN_FORMAT = ('markdown_strict+'
                          'fancy_lists+'
                          'startnum+'
                          'backtick_code_blocks+'
                          'tex_math_dollars'
                          )


def pandoc(obj, to, **kwargs):
    """Convert a string or a file with pandoc."""
    import pypandoc
    return pypandoc.convert(obj, to, **kwargs)


def get_pandoc_formats():
    import pypandoc
    return pypandoc.get_pandoc_formats()


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
