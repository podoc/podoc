# -*- coding: utf-8 -*-

"""CLI tool."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
import sys

import click

from podoc import __version__, Podoc
from podoc.utils import _shorten_string

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# CLI
#------------------------------------------------------------------------------

@click.command()
@click.argument('files',
                # TODO: nargs=-1 for multiple files concat
                required=False,
                type=click.Path(exists=True, file_okay=True,
                                dir_okay=True, resolve_path=True))
@click.option('-f', '-r', '--from', '--read', default='markdown')
@click.option('-t', '-w', '--to', '--write', default='ast')
@click.option('-o', '--output')
@click.option('--data-dir')
@click.option('--no-pandoc', default=False, is_flag=True)
@click.version_option(__version__)
@click.help_option()
def podoc(files=None,
          read=None,
          write=None,
          output=None,
          data_dir=None,
          no_pandoc=False,
          ):
    """Convert one or several files from a supported format to another."""
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
        out = podoc.convert(contents, source=read, target=write,
                            output=output)
    else:
        # TODO: multiple files
        logger.debug("Converting file `%s` from %s to %s in %s.",
                     files, read, write, output)
        out = podoc.convert(files, source=read, target=write, output=output)
    if output is None:
        click.echo(podoc.dumps(out, write))
        return


if __name__ == '__main__':  # pragma: no cover
    podoc()
