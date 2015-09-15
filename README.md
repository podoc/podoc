# podoc

[![Build Status](https://img.shields.io/travis/podoc/podoc.svg)](https://travis-ci.org/podoc/podoc)
[![codecov.io](https://img.shields.io/codecov/c/github/podoc/podoc.svg)](http://codecov.io/github/podoc/podoc?branch=master)
[![Documentation Status](https://readthedocs.org/projects/podoc/badge/?version=latest)](https://readthedocs.org/projects/podoc/?badge=latest)
[![PyPI release](https://img.shields.io/pypi/v/podoc.svg)](https://pypi.python.org/pypi/podoc)
[![GitHub release](https://img.shields.io/github/release/podoc/podoc.svg)](https://github.com/podoc/podoc/releases/latest)
[![Join the chat at https://gitter.im/podoc/podoc](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/podoc/podoc?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)


[![podoc](http://www.theturtlesource.com/turtleContainer/unifilusTOP.jpg)](https://en.wikipedia.org/wiki/Podocnemididae)

**This is a work in progress**

**podoc** is a **minimalistic pure Python pandoc clone**, i.e. a markup document conversion library. Currently, it supports Markdown, Jupyter notebook, OpenDocument, O'Reilly Atlas, Python + comments. Support for ReST, LaTeX, HTML, AsciiDoc is planned.

podoc provides a Python API as well as a command-line tool. The architecture is modular and allows for the creation of plugins, custom formats, readers, writers, preprocessors, postprocessors, and filters.

podoc is heavily inspired by the awesome **pandoc** library: It tries to mimic the abstractions and API when possible, but it does not intend to reproduce the full set of features. podoc also borrows ideas and code from the **mistune** Markdown parser. An earlier version of the code lives in the ipymd repository.

podoc is released under the BSD license.


## Why another pandoc clone?

pandoc is written in Haskell. Python wrappers generally call pandoc through a system call, which is a bit limited in terms of functionality and performance. Also, the dependency to the pandoc executable is a barrier to some Python projects.

podoc provides both a command-line tool and a complete and flexible Python API. It has no dependency, but it has far less features than pandoc and supports many less formats. However, podoc supports the Jupyter Notebook format natively and provides a Jupyter extension for on-the-fly document conversion in the Notebook. This means you can read and edit non-notebook documents in the Jupyter Notebook, including documents written in Markdown, OpenOffice, and any format supported by podoc. As such, podoc replaces the previous ipymd library.

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
* Built-in set of preprocessors and postprocessors
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

* **Preprocessors** (optional): the input document can be processed before the conversion.
* **Reader**: the processed input document is parsed and transformed into an in-memory **Abstract Syntax Tree** (AST). The AST is fully JSON-serializable.
* **Filters** (optional): filters can transform the AST.
* **Writer**: a writer transforms the filtered AST into an output document.
* **Postprocessors** (optional): the output document can be processed after the conversion.

### Formats

With podoc, there is no dedicated abstraction for a *format*. A format is just a plugin that implements a reader and/or a writer, with optional filters and pre- and postprocessors.

### Podoc class

The `Podoc` class represents a given conversion pipeline. Here are its trait attributes:

* `output_dir`: output directory
* `preprocessors`
* `reader`
* `filters`
* `writer`
* `postprocessors`

Here are its main methods:

* `convert_file(from_path, to_path=None)`
* `convert_contents(contents, to_path=None)`
* `add_preprocessor(func)`
* `set_reader(func)`
* `add_filter(func)`
* `set_writer(func)`
* `add_postprocessor(func)`

### Configuration

podoc uses the `traitlets` module for the configuration system (the same as in IPython).

### Plugins

The plugin architecture is inspired by this [blog post](http://eli.thegreenplace.net/2012/08/07/fundamental-concepts-of-plugin-infrastructures).

To create a plugin, create a Python script in one of the plugin directories, and define a class deriving from `podoc.IPlugin`:

```python
class MyPlugin(IPlugin):
    format_name  # optional: if set, one can use this name as an alias
    file_extensions  # optional: list of supported file extensions

    def preprocessor(self, contents):
        return contents

    def register(self):
        self.podoc.add_preprocessor(self.preprocessor)
...
```

Then, use the following command:

```bash
podoc myfile.xxx -o myfile.yyy --plugins=MyPlugin
```

This will use the preprocessor defined in `MyPlugin`.

In the plugin, you have access to `self.podoc`, the `Podoc` instance.

You can also use other methods:

* `preprocessor(contents)`
* `reader(contents)`
* `filter(ast)`
* `writer(ast)`
* `postprocessor(contents)`

There is a `podoc-contrib` repository with common user-contributed plugins.

You can edit `default_plugins` in your `.podoc/config.py`.

Every Python file in `.podoc/plugins/` will be automatically imported when using podoc. If plugins are defined there, they will be readily available in podoc.

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

### Included plugins

* `Atlas`: filter replacing code blocks in a given language by executable `<pre>` HTML code blocks, and LaTeX equations by `<span>` HTML blocks.
* `CodeEval`: preprocessor evaluating code enclosed in particular markup syntax (as provided by a regular expression). This allows for **literate programming**, using Python or any other language.
* `Macros`: macro preprocessor based on regular expressions. The macro substitutions can be listed in the `macros` metadata array in the document, or in `c.Macros.substitutions = [(regex, repl), ...]` in your `.podoc/config.py`.
* `Prompt`: filter transforming a code block containing interactive input and output. There are several options:
    * Transforming to a code block with different input/output formats
    * Removing the output
    * Evaluating the input and adding the output
    * Put the output in a paragraph


## Code structure

```
docs/
examples/
podoc/
    plugins/
        markdown/
            examples/
                hello_world/
                    input.md
                    output.json
            tests/
        notebook/
            examples/
            tests/
        opendocument/
            examples/
            tests/
        python/
            examples/
            tests/
        macros.py
        atlas.py
        code_eval.py
        prompt.py
    tests/                      unit tests
    __init__.py
    core.py
    logging.py
    script.py                   CLI tool based on the click library
tests/                          integration tests
utils/
    make_examples.py            build output files in examples, using pandoc
```
