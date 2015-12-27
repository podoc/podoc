# podoc

[![Build Status](https://img.shields.io/travis/podoc/podoc.svg)](https://travis-ci.org/podoc/podoc)
[![codecov.io](https://img.shields.io/codecov/c/github/podoc/podoc.svg)](http://codecov.io/github/podoc/podoc?branch=master)
[![Documentation Status](https://readthedocs.org/projects/podoc/badge/?version=latest)](https://readthedocs.org/projects/podoc/?badge=latest)
[![PyPI release](https://img.shields.io/pypi/v/podoc.svg)](https://pypi.python.org/pypi/podoc)
[![GitHub release](https://img.shields.io/github/release/podoc/podoc.svg)](https://github.com/podoc/podoc/releases/latest)
[![Join the chat at https://gitter.im/podoc/podoc](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/podoc/podoc?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)


[![podoc](http://www.theturtlesource.com/turtleContainer/unifilusTOP.jpg)](https://en.wikipedia.org/wiki/Podocnemididae)

**This is a work in progress**

**podoc** is a **minimalistic pure Python pandoc companion**, i.e. a markup document conversion library **compatible with pandoc**. The plan is for podoc to support Markdown, Jupyter Notebook, OpenDocument, O'Reilly Atlas, Python + comments. Support for ReST, LaTeX, HTML, AsciiDoc is planned.

podoc provides a Python API as well as a command-line tool. The architecture is modular and allows for the creation of plugins, custom formats, readers, writers, prefilters, postfilters, and filters.

podoc is heavily inspired by the awesome **pandoc** library: It tries to use the same abstractions, API, and internal format, but it does not intend to reproduce the full set of features. Instead, **podoc uses the same internal AST than pandoc for compatibility**.

podoc also borrows ideas and code from the **mistune** Markdown parser. An earlier version of podoc lives in the ipymd repository.

podoc is released under the BSD license.


## Why?

pandoc is written in Haskell. Python wrappers generally call pandoc through a system call, which is a bit limited in terms of functionality and performance. Also, the dependency to the pandoc executable is a barrier to some Python projects.

podoc provides both a command-line tool and a complete and flexible Python API. It has no dependency, but it has far less features than pandoc and supports many less formats. However, podoc supports the Jupyter Notebook format natively and provides a Jupyter extension for on-the-fly document conversion in the Notebook. This means you can read and edit non-notebook documents in the Jupyter Notebook, including documents written in Markdown, OpenOffice, and any format supported by podoc and pandoc. As such, podoc replaces the previous ipymd library.

In the long run, podoc could also share code with Jupyter nbconvert.


## Installation

podoc requires Python 3.4+. Support for Python 2.7 might be considered in the future if there is sufficient demand.

To install podoc, type the following command in a terminal:

```bash
pip install podoc
```


## Usage

The most common usage is the same as pandoc:

```
podoc -f foo -t bar file.xxx -o file.yyy
```

The formats can also be inferred from the file extensions.

The list of currently supported formats is:

* `markdown`
* `notebook`
* `opendocument`
* `python`

podoc can read and write in all of these formats.


## Examples and applications

* Conversion of Jupyter notebooks
* Use the Jupyter frontend with non-`.ipynb` documents
* Write slide shows in Markdown
* Write technical documents or books in Markdown with LaTeX equations, and convert them to HTML, ODT, or PDF
* Literate programming
* Doc tests
* Automatic documentation generation
* Static website generation

Examples can be found in the `examples` directory. Every example is in a subdirectory containing the following files:

* `input.xxx`
* `output.yyy`
* `convert.sh`: a podoc command that converts `input.xxx` into `output.yyy`

All examples are automatically checked as part of podoc's testing suite.

## Advanced documentation

### Features

* Command-line tool
* Full Python API
* Native support for Jupyter notebooks
* Fully customizable transformation pipeline
* Built-in set of prefilters and postfilters
* Global and block metadata
* LaTeX equations
* Templates

The following features (supported by pandoc) may or may not be considered in the future:

* Bibliography
* Tables
* Markdown extensions
* Slide shows

### Pipeline

podoc uses the following pipeline to convert a document:

* **FileOpener**: open a `Document` from a file. Generally, a `Document` is just a string for text files, but other openers can be defined for binary file formats like OpenDocument.
* **Prefilters** (optional): the input document can be filtered before the conversion.
* **Reader**: the filtered input document is parsed and transformed into an in-memory **Abstract Syntax Tree** (AST). The AST is fully JSON-serializable.
* **Filters** (optional): filters can transform the AST.
* **Writer**: a writer transforms the filtered AST into an output document.
* **Postfilters** (optional): the output document can be filtered after the conversion.
* **FileSaver**: save a `Document` into a file.

### Formats

With podoc, there is no dedicated abstraction for a *format*. A format is just a plugin that defines a file opener/file saver, a reader and/or a writer, optional filters, and optional pre- and postfilters.

### Podoc class

The `Podoc` class represents a given conversion pipeline. Here are its attributes:

* `output_dir`: output directory
* `file_opener`
* `prefilters`
* `reader`
* `filters`
* `writer`
* `postfilters`
* `file_saver`

Here are its main methods:

* `convert_file(from_path, to_path=None)`
* `convert_contents(contents, to_path=None)`
* `set_file_opener(func)`
* `add_prefilter(func)`
* `set_reader(func)`
* `add_filter(func)`
* `set_writer(func)`
* `add_postfilter(func)`
* `set_file_saver(func)`

### Configuration

podoc uses the `traitlets` module for the configuration system (the same as in IPython).

### AST

Every document is converted into a native representation called the AST (the same as in pandoc). This is a tree with a `Meta` block (containing hierarchical metadata like title, authors, and date) and a list of `Block` elements. Each `Block` contains a `Meta` element and a list of `Inline` elements.

* [List of Block elements](http://hackage.haskell.org/package/pandoc-types-1.12.4.5/docs/Text-Pandoc-Definition.html#t:Block)
* [List of Inline elements](http://hackage.haskell.org/package/pandoc-types-1.12.4.5/docs/Text-Pandoc-Definition.html#t:Inline)

The `AST` class derives from `dict` and provides the following interface:

```python
>>> ast.meta
{...}
>>> ast.blocks
[<Block ...>, <Block ...>, ...]
>>> block = ast.blocks[0]
>>> block.meta
{...}
>>> block.inline
["str", <Inline ...>, ...]
>>> block.inline[1]
["str", "str"]
>>> ast.validate()  # check that this is a valid AST
True
```

When converted to JSON, each element has the following fields (this corresponds to the pandoc JSON format):

* `t`: the name of the `Block` or `Inline` element
* `c`: a string, or a list of `Inline` elements

### Plugins

The plugin architecture is inspired by this [blog post](http://eli.thegreenplace.net/2012/08/07/fundamental-concepts-of-plugin-infrastructures).

To create a plugin, create a Python script in one of the plugin directories, and define a class deriving from `podoc.IPlugin`:

```python
class MyPlugin(IPlugin):
    file_extensions  # optional: list of supported file extensions
...
```

You can implement the following methods:

* `opener(path)`
* `prefilter(contents)`
* `reader(contents)`
* `filter(ast)`
* `writer(ast)`
* `postfilter(contents)`
* `saver(path, contents)`

For more fine-grained capabilities, you can also implement `attach(podoc, steps)` and `set_<step>(podoc)` for all steps. See the implementation of `IPlugin` for more details.

Then, use the following command:

```bash
podoc myfile.xxx -o myfile.yyy --plugins=MyPlugin
```

You can also use the `--from` and `--to` parameters to specify the plugins to use for the input and output documents.

If no input/output plugins are specified, podoc will look at the file extensions and activate the plugins that have registered themselves with these extensions. If several plugins try to register themselves for the reader or writer, an exception is raised (only one reader/writer is allowed).

There is a `podoc-contrib` repository with common user-contributed plugins.

You can edit `default_plugins` in your `.podoc/config.py`.

Every Python file in `.podoc/plugins/` will be automatically imported when using podoc. If plugins are defined there, they will be readily available in podoc.

Ideally, every plugin should be in a dedicated subdirectory with a `README.md` documentation file.

### Included plugins

* `Atlas`: filter replacing code blocks in a given language by executable `<pre>` HTML code blocks, and LaTeX equations by `<span>` HTML blocks.
* `CodeEval`: prefilter evaluating code enclosed in particular markup syntax (as provided by a regular expression). This allows for **literate programming**, using Python or any other language.
* `Macros`: macro prefilter based on regular expressions. The macro substitutions can be listed in the `macros` metadata array in the document, or in `c.Macros.substitutions = [(regex, repl), ...]` in your `.podoc/config.py`.
* `Prompt`: filter transforming a code block containing interactive input and output. There are several options:
    * Transforming to a code block with different input/output formats
    * Removing the output
    * Evaluating the input and adding the output
    * Put the output in a paragraph
* `UrlChecker`: find all broken hypertext links.
