# -*- coding: utf-8 -*-

"""Test Notebook plugin."""


#-------------------------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------------------------

from podoc.utils import get_test_file_path, Bunch
from .._utils import extract_image, extract_table

from .._notebook import (output_filename,
                         open_notebook,
                         )


#-------------------------------------------------------------------------------------------------
# Test Notebook utils
#-------------------------------------------------------------------------------------------------

def test_extract_image():
    # Open a test notebook with a code cell containing an image.
    path = get_test_file_path('notebook', 'simplenb.ipynb')
    notebook = open_notebook(path)
    cell = notebook.cells[4]
    mime_type, data = list(extract_image(cell.outputs[1]))
    filename = output_filename(mime_type, cell_index=4, output_index=1)
    assert filename == 'output_4_1.png'

    # Open the image file in the markdown directory.
    image_path = get_test_file_path('markdown', 'simplenb_files/simplenb_4_1.png')
    with open(image_path, 'rb') as f:
        data_expected = f.read()

    # The two image contents should be identical.
    assert data == data_expected


def test_extract_table():
    html = '<table><tr><td>hello</td></tr></table>'
    output = Bunch(data=Bunch({'text/html': html}))
    _, data = extract_table(output)
    assert data[:4] == b'\x89PNG'
