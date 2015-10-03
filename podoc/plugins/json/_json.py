# -*- coding: utf-8 -*-

"""JSON plugin."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import json
import logging

from podoc.ast import from_json, to_json
from podoc.plugin import IPlugin

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# JSON plugin
#------------------------------------------------------------------------------

class JSON(IPlugin):
    file_extensions = ('.json',)

    def opener(self, path):
        """Open a file and return a file handle."""
        logger.debug("Open JSON file `%s`.", path)
        with open(path, 'r') as f:
            return json.load(f)

    def reader(self, contents):
        """Convert a JSON file handle to an AST."""
        return from_json(contents)

    def writer(self, ast):
        """Convert an AST to a JSON dict."""
        return to_json(ast)

    def saver(self, path, contents):
        """Save a JSON dict to a file."""
        # path, json_dict -> None
        logger.debug("Save JSON file `%s`.", path)
        json.dump(contents, path, sort_keys=True, indent=2)
        return contents
