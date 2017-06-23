# -*- coding: utf-8 -*-

"""Utility functions."""

from contextlib import contextmanager
from io import StringIO
import json
import logging
import os
import os.path as op
import sys

logger = logging.getLogger(__name__)


#-------------------------------------------------------------------------------------------------
# Bunch
#-------------------------------------------------------------------------------------------------

class Bunch(dict):
    """A dict with additional dot syntax."""
    def __init__(self, *args, **kwargs):
        super(Bunch, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def copy(self):
        return Bunch(super(Bunch, self).copy())


#-------------------------------------------------------------------------------------------------
# File I/O
#-------------------------------------------------------------------------------------------------

def load_text(path):
    assert op.exists(path)
    with open(path, 'r') as f:
        out = f.read()
    return out


def dump_text(contents, path):
    with open(path, 'w') as f:
        return f.write(contents)


def _get_file(file_or_path, mode=None):
    if isinstance(file_or_path, str):
        return open(file_or_path, mode)
    else:
        return file_or_path


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def _shorten_string(s, lim=40):
    return s if len(s) <= lim else (s[:lim // 2] + ' (...) ' + s[-lim // 2:])


#-------------------------------------------------------------------------------------------------
# Resources
#-------------------------------------------------------------------------------------------------

def _get_resources_path(doc_path):
    assert doc_path
    doc_path = op.realpath(doc_path)
    fn = op.basename(doc_path)
    fn = op.splitext(fn)[0]
    return op.join(op.dirname(doc_path), '%s_files' % fn)


def _save_resources(resources, res_path=None):
    if not resources:
        return
    if not res_path:
        logger.debug("No resource path given.")
        return
    if not op.exists(res_path):
        logger.debug("Create directory `%s`.", res_path)
        os.makedirs(res_path)
    resources = resources or {}
    for fn, data in resources.items():
        path = op.join(res_path, fn)
        with open(path, 'wb') as f:
            logger.debug("Writing %d bytes to `%s`.", len(data), path)
            f.write(data)


def _load_resources(res_path):
    if not res_path:
        logger.debug("No resource path given.")
        return {}
    resources = {}
    # List all files in the resources path.
    if not op.exists(res_path) or not op.isdir(res_path):
        return resources
    for fn in os.listdir(res_path):
        path = op.join(res_path, fn)
        with open(path, 'rb') as f:
            data = f.read()
        logger.debug("Read %d bytes from `%s`.", len(data), path)
        resources[fn] = data
    return resources


#-------------------------------------------------------------------------------------------------
# Path
#-------------------------------------------------------------------------------------------------

def _normalize_path(path):
    assert isinstance(path, str)
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


#-------------------------------------------------------------------------------------------------
# Testing utils
#-------------------------------------------------------------------------------------------------

def get_test_file_path(lang, filename):
    curdir = op.realpath(op.dirname(__file__))
    # Construct the directory name for the language and test filename.
    dirname = op.realpath(op.join(curdir, lang))
    path = op.join(dirname, 'test_files', filename)
    assert op.exists(path)
    return path


def _merge_str(l):
    """Concatenate consecutive strings in a list of nodes."""
    out = []
    for node in l:
        if (out and isinstance(out[-1], str) and
                isinstance(node, str)):
            out[-1] += node
        else:
            out.append(node)
    return out


#-------------------------------------------------------------------------------------------------
# pandoc wrapper
#-------------------------------------------------------------------------------------------------

# TODO: commonmark instead
PANDOC_MARKDOWN_FORMAT = ('markdown_strict'
                          '-raw_html+'
                          'fancy_lists+'
                          'startnum+'
                          'backtick_code_blocks+'
                          'hard_line_breaks+'
                          'tex_math_dollars'
                          )


def pandoc(obj, to, **kwargs):
    """Convert a string or a file with pandoc."""
    import pypandoc
    return pypandoc.convert(obj, to, **kwargs)


def get_pandoc_formats():
    import pypandoc
    return pypandoc.get_pandoc_formats()


def get_pandoc_api_version():
    import pypandoc
    return json.loads(pypandoc.convert_text('', 'json', format='markdown'))['pandoc-api-version']


PANDOC_API_VERSION = get_pandoc_api_version()


def has_pandoc():  # pragma: no cover
    try:
        with captured_output():
            import pypandoc
            pypandoc.get_pandoc_version()
        return True
    except (OSError, ImportError):
        logger.info("pypandoc is not installed.")
    except FileNotFoundError:
        logger.info("pandoc is not installed.")
    return False


def generate_json_test_files():  # pragma: no cover
    """Regenerate all *.json files in ast/test_files."""
    curdir = op.realpath(op.dirname(__file__))
    directory = op.join(curdir, 'markdown', 'test_files')
    files = os.listdir(directory)
    for file in files:
        if file.endswith('.md'):
            path = op.join(directory, file)
            out = pandoc(load_text(path), 'json',
                         format=PANDOC_MARKDOWN_FORMAT)
            base = op.splitext(file)[0]
            path_json = op.join(curdir, 'ast', 'test_files', base + '.json')
            with open(path_json, 'w') as fw:
                d = json.loads(out)
                json.dump(d, fw, sort_keys=True, indent=2)
