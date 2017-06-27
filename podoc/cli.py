# -*- coding: utf-8 -*-

"""CLI tool."""


#-------------------------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------------------------

import logging
import sys
import textwrap

import click

from podoc import __version__, Podoc
from podoc.utils import _shorten_string

logger = logging.getLogger(__name__)


#-------------------------------------------------------------------------------------------------
# CLI
#-------------------------------------------------------------------------------------------------

PODOC_HELP = """Convert a file or a string from one format to another.

\b
{}
\b
{}
"""


def _wrap(languages, lead=''):
    if not languages:  # pragma: no cover
        return lead
    l = ', '.join(languages)
    lines = textwrap.wrap(l, 70 - len(lead))
    out = lead + lines[0] + '\n'
    out += '\n'.join(((' ' * len(lead)) + line) for line in lines[1:])
    return out


def get_podoc_languages():
    """Return the list of languages without/with pandoc."""
    l0 = Podoc(with_pandoc=False).languages
    l1 = Podoc(with_pandoc=True).languages
    l1 = [_ for _ in l1 if _ not in l0]
    return l0, l1


def get_podoc_docstring():
    """Generate the podoc CLI help string."""
    l0, l1 = get_podoc_languages()
    return PODOC_HELP.format(_wrap(l0, 'native formats: '),
                             _wrap(l1, 'pandoc formats: '))


PODOC_HELP = get_podoc_docstring()


@click.command(help=PODOC_HELP)
@click.argument('files',
                nargs=-1,
                required=False,
                type=click.Path(exists=True, file_okay=True,
                                dir_okay=True, resolve_path=True))
@click.option('-f', '-r', '--from', '--read',
              help='Source format.')
@click.option('-t', '-w', '--to', '--write',
              help='Target format.')
@click.option('-o', '--output',
              type=click.Path(exists=False, file_okay=True,
                              dir_okay=False, resolve_path=True),
              help='Output path.')
@click.option('-d', '--output-dir',
              type=click.Path(exists=False, file_okay=False,
                              dir_okay=True, resolve_path=True),
              help='Output directory.')
@click.option('--no-pandoc', default=False, is_flag=True,
              help='Disable pandoc formats.')
@click.version_option(__version__)
@click.help_option()
def podoc(files=None,
          read=None,
          write=None,
          output=None,
          output_dir=None,
          no_pandoc=False,
          ):
    """Convert a file or a string from one format to another."""
    # Create the Podoc instance.
    podoc = Podoc(with_pandoc=not(no_pandoc))
    # If no files are provided, read from the standard input (like pandoc).
    if not files:
        logger.debug("Reading contents from stdin...")
        contents_s = ''.join(sys.stdin.readlines())
        # From string to object.
        contents = podoc.loads(contents_s, read)
        logger.debug("Converting `%s` from %s to %s (file: `%s`).",
                     _shorten_string(contents_s),
                     read, write, output,
                     )
        out = podoc.convert_text(contents, source=read, target=write,
                                 output=output)
    else:
        out = podoc.convert_files(files, source=read, target=write,
                                  output=output, output_dir=output_dir)
    if output is None and output_dir is None:
        click.echo(podoc.dumps(out, write))


if __name__ == '__main__':  # pragma: no cover
    podoc()
