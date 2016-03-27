# -*- coding: utf-8 -*-

"""CLI tool."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
import os.path as op
import sys

import click

from podoc import __version__, Podoc

logger = logging.getLogger(__name__)


#------------------------------------------------------------------------------
# CLI
#------------------------------------------------------------------------------

@click.command()
@click.argument('files', nargs=-1,
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
        contents = ''.join(sys.stdin.readlines())
        out = podoc.convert(contents, source=read, target=write)
    else:
        # TODO: concatenate non-string objects. For now we assume that
        # output1 + output2 just works.
        out = sum(podoc.convert(file, source=read, target=write)
                  for file in files)
    if output is None:
        click.echo(out)
        return
    # Save the output.
    path = output if not data_dir else op.join(data_dir, output)
    podoc.save(path, out, lang=write)


if __name__ == '__main__':  # pragma: no cover
    podoc()
