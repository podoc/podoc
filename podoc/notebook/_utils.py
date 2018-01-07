# -*- coding: utf-8 -*-

"""Notebook utilities."""


#-------------------------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------------------------

import base64
import logging
import os
import os.path as op
import subprocess
import sys
import tempfile

from IPython.lib.latextools import genelatex

logger = logging.getLogger(__name__)


#-------------------------------------------------------------------------------------------------
# Utilities
#-------------------------------------------------------------------------------------------------

_EXTRACT_OUTPUT_TYPES = ('image/png',
                         'image/jpeg',
                         'image/svg+xml',
                         'application/pdf',
                         )


_TABLE_STYLES = '''
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<style>
table {
    margin-left: auto;
    margin-right: auto;
    border: none;
    border-collapse: collapse;
    border-spacing: 0;
    color: black;
    font-size: 12px;
    table-layout: fixed;
}
thead {
    border-bottom: 1px solid black;
    vertical-align: bottom;
}
tr, th, td {
    text-align: right;
    vertical-align: middle;
    padding: 0.5em 0.5em;
    line-height: 1.0;
    white-space: nowrap;
    max-width: 100px;
    text-overflow: ellipsis;
    overflow: hidden;
    border: none;
    font-family: "Helvetica Neue", Arial, Helvetica, Geneva, sans-serif;
}
th {
    font-weight: bold;
}
tbody tr:nth-child(odd) {
    background: #f5f5f5;
}
</style>
'''


def latex_to_png_base64(latex):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = os.path.join(tmpdir, "tmp.tex")
        dvifile = os.path.join(tmpdir, "tmp.dvi")
        pngfile = os.path.join(tmpdir, "tmp.png")

        contents = list(genelatex(latex, False))
        with open(tmpfile, "w") as f:
            f.writelines(contents)

        with open(os.devnull, 'w') as devnull:
            try:
                subprocess.check_call(
                    ["latex", "-halt-on-error", tmpfile], cwd=tmpdir,
                    stdout=devnull, stderr=devnull)
            except Exception as e:
                print("************")
                print(len(contents))
                print('\n'.join(contents))
                raise(e)

            subprocess.check_call(
                ["dvipng", "-T", "tight", "-x", "6000", "-z", "9",
                 "-bg", "transparent", "-o", pngfile, dvifile], cwd=tmpdir,
                stdout=devnull, stderr=devnull)

        with open(pngfile, 'rb') as f:
            return base64.b64encode(f.read())


def extract_image(output):
    """Return the output mime type and data for the first found mime type.

    https://github.com/jupyter/nbconvert/blob/master/nbconvert/preprocessors/extractoutput.py

    Copyright (c) IPython Development Team.
    Distributed under the terms of the Modified BSD License.

    """

    # HACK: SymPy PNG output is low resolution but it comes with LaTeX source.
    # We override the low PNG with a high-resolution one.
    if 'image/png' in output.data and 'text/latex' in output.data:
        latex = ''.join(output.data['text/latex'])
        b64 = latex_to_png_base64(latex)
        output.data['image/png'] = b64

    # Get the output in data formats that the template needs extracted.
    for mime_type in _EXTRACT_OUTPUT_TYPES:
        if mime_type not in output.data:
            continue
        data = output.data[mime_type]

        # Binary files are base64-encoded, SVG is already XML.
        if mime_type in {'image/png', 'image/jpeg', 'application/pdf'}:
            # data is b64-encoded as text (str, unicode)
            # decodestring only accepts bytes

            # from IPython.utils import py3compat
            # data = py3compat.cast_bytes(data)
            if not isinstance(data, bytes):
                data = data.encode('UTF-8', 'replace')

            try:
                data = base64.decodestring(data)
            except Exception as e:  # pragma: no cover
                logger.warn("Unable to decode: %s.", str(e))
                data = b''
        elif sys.platform == 'win32':  # pragma: no cover
            data = data.replace('\n', '\r\n').encode('UTF-8')
        else:  # pragma: no cover
            data = data.encode('UTF-8')

        return mime_type, data


def extract_table(output):
    # Process HTML output.
    html = output.data.get('text/html', None)
    if not html:
        return
    with tempfile.TemporaryDirectory() as tmpdir:
        # File paths.
        in_path = op.join(tmpdir, 'source.html')
        out_path = op.join(tmpdir, 'img.pdf')
        out_path2 = op.join(tmpdir, 'img.png')
        # Add table styles.
        html = _TABLE_STYLES + html
        with open(in_path, 'w') as f:
            f.write(html)
        os.system('wkhtmltopdf -q %s %s' % (in_path, out_path))
        os.system(('convert -density 300 -trim -border 20x20 '
                   '-bordercolor white -background white'
                   ' -alpha remove %s %s') % (out_path, out_path2))
        with open(out_path2, 'rb') as f:
            data = f.read()
    return 'image/png', data
