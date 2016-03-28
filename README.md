# podoc

[![Build Status](https://img.shields.io/travis/podoc/podoc.svg)](https://travis-ci.org/podoc/podoc)
[![codecov.io](https://img.shields.io/codecov/c/github/podoc/podoc.svg)](http://codecov.io/github/podoc/podoc?branch=master)
[![Documentation Status](https://readthedocs.org/projects/podoc/badge/?version=latest)](https://readthedocs.org/projects/podoc/?badge=latest)
[![PyPI release](https://img.shields.io/pypi/v/podoc.svg)](https://pypi.python.org/pypi/podoc)
[![GitHub release](https://img.shields.io/github/release/podoc/podoc.svg)](https://github.com/podoc/podoc/releases/latest)
[![Join the chat at https://gitter.im/podoc/podoc](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/podoc/podoc?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

**podoc** is a document conversion library in Python. Natively, it supports Markdown and Jupyter Notebook. More formats will be added later.

podoc will be able to convert documents on the fly in the Jupyter Notebook, so you can use the Notebook directly on Markdown documents. This feature was previously implemented in [**ipymd**](https://github.com/rossant/ipymd).


## Links with pandoc

podoc has strong links with [**pandoc**](http://pandoc.org/), a universal document converted in Haskell. Both libraries use the same intermediate representation, so you can combine them seamlessly.

**You don't need pandoc to install and use podoc**. However, you'll have many more conversion options if pandoc is installed. Note that we systematically test the compatibility of podoc with the [latest release of pandoc](https://github.com/jgm/pandoc/releases/latest). If you want to use pandoc with podoc, make sure that you have the latest version installed.

The compatibility with pandoc enables many interesting use-cases.


## Command-line tool

podoc provides a `podoc` command-line tool that is quite similar to `pandoc`.

```bash
$ podoc --help
Usage: podoc [OPTIONS] [FILES]

  Convert one or several files from a supported format to another.

Options:
  -f, -r, --from, --read TEXT
  -t, -w, --to, --write TEXT
  -o, --output TEXT
  --data-dir TEXT
  --no-pandoc
  --version                    Show the version and exit.
  --help                       Show this message and exit.
```

Like `pandoc`, if no files are provided on the command line, podoc takes its input on stdin.


## Use-cases

### Writing Markdown documents in the Jupyter Notebook

### Quickly creating a new Jupyter notebook from the command-line



## Plugin ideas

podoc features a simple plugin system that allows you to implement custom transformation functions. Here are a few plugin ideas:

* `ASCIIImage`: replace images by ASCII art to display documents with images in the console.
* `Atlas`: filter replacing code blocks in a given language by executable `<pre>` HTML code blocks, and LaTeX equations by `<span>` HTML blocks. This is used by the O'Reilly Atlas platform.
* `CodeEval`: evaluate some code elements and replace them by their output. This allows for **literate programming** using Python.
* `Graph`: describe a graph or a tree in a human-readable format and have it converted automatically to an image (e.g. [mermaid](http://knsv.github.io/mermaid/))
* `Include`: just include several documents in a single document.
* `Macros`: perform regex substitutions. The macro substitutions can be listed in the `macros` metadata array in the document, or in `c.Macros.substitutions = [(regex, repl), ...]` in your `.podoc/podoc_config.py`.
* `Prompt`: parse and write prompt prefix in an input code cell.
* `SlideShow`: read and write slideshows
* `UrlChecker`: find all broken hypertext links and generate a report.
