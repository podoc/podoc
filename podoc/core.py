# -*- coding: utf-8 -*-
# flake8: noqa

"""Core functionality."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
import os
import os.path as op


#------------------------------------------------------------------------------
# Main class
#------------------------------------------------------------------------------

class Podoc(object):
    """Conversion pipeline for markup documents.

    This class implements the core conversion functionality of podoc.

    """
    file_opener = None
    preprocessors = ()
    reader = None
    filters = ()
    writer = None
    postprocessors = ()
    file_saver = None

    # Individual stages
    # -------------------------------------------------------------------------

    def open(self, path):
        assert self.file_opener is not None
        return self.file_opener.open(path)

    def save(self, path, contents):
        assert self.file_saver is not None
        return self.file_saver.save(path, contents)

    def preprocess(self, contents):
        for p in self.preprocessors:
            contents = p(contents)
        return contents

    def read(self, contents):
        assert self.reader is not None
        ast = self.reader(contents)
        return ast

    def filter(self, ast):
        for f in self.filters:
            ast = f(ast)
        return ast

    def write(self, ast):
        assert self.writer is not None
        converted = self.writer(ast)
        return converted

    def postprocess(self, contents):
        for p in self.postprocessors:
            contents = p(contents)
        return contents

    # Main methods
    # -------------------------------------------------------------------------

    def convert_file(self, from_path, to_path):
        document = self.open(from_path)
        converted = self.convert_contents(document)
        self.saver(to_path, converted)

    def convert_contents(self, contents):
        contents = self.preprocess(contents)
        ast = self.read(contents)
        ast = self.filter(ast)
        converted = self.write(ast)
        converted = self.postprocess(converted)
        return converted

    # Pipeline configuration
    # -------------------------------------------------------------------------

    def add_preprocessor(self, func):
        self.preprocessors.append(func)

    def set_reader(self, func):
        self.reader = func

    def add_filter(self, func):
        self.filters.append(func)

    def set_writer(self, func):
        self.writer = func

    def add_postprocessor(self, func):
        self.postprocessors.append(func)
