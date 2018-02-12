# podoc


[![Build Status](https://img.shields.io/travis/podoc/podoc.svg)](https://travis-ci.org/podoc/podoc)
[![codecov.io](https://img.shields.io/codecov/c/github/podoc/podoc.svg)](http://codecov.io/github/podoc/podoc?branch=master)
[![Documentation Status](https://readthedocs.org/projects/podoc/badge/?version=latest)](https://readthedocs.org/projects/podoc/?badge=latest)
[![PyPI release](https://img.shields.io/pypi/v/podoc.svg)](https://pypi.python.org/pypi/podoc)
[![GitHub release](https://img.shields.io/github/release/podoc/podoc.svg)](https://github.com/podoc/podoc/releases/latest)
[![Join the chat at https://gitter.im/podoc/podoc](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/podoc/podoc?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

**Experimental project: use at your own risks**

**podoc** is a document conversion library in Python. Natively, it supports Markdown and Jupyter Notebook. More formats will be added later.

podoc also allows you to convert documents on the fly in the Jupyter Notebook, so you can use the Notebook directly on documents in Markdown and many other formats. This feature was previously implemented in [**ipymd**](https://github.com/rossant/ipymd).

## Relations with pandoc

podoc is based on [**pandoc**](http://pandoc.org/), a universal document converted in Haskell. Both libraries use the same intermediate representation (JSON-serializable Abstract Syntax Tree, or AST), so you can combine them seamlessly. We systematically test the compatibility of podoc with the [latest release of pandoc](https://github.com/jgm/pandoc/releases/latest). If you want to use pandoc with podoc, make sure that you have the latest version installed.

The compatibility with pandoc enables many interesting use-cases.

## Command-line tool

podoc provides a `podoc` command-line tool that is quite similar to `pandoc`.

```bash
$ podoc --help
Usage: podoc [OPTIONS] [FILES]

  Convert a file or a string from one format to another.

  native formats: ast, markdown, notebook

  pandoc formats: asciidoc, beamer, commonmark, context, docbook, docx,
                  dokuwiki, dzslides, epub, epub3, fb2, haddock, html,
                  html5, icml, json, latex, man, markdown_github,
                  markdown_mmd, markdown_phpextra, markdown_strict,
                  mediawiki, native, odt, opendocument, opml, org, pdf,
                  plain, revealjs, rst, rtf, s5, slideous, slidy, t2t,
                  tei, texinfo, textile, twiki

Options:
  -f, -r, --from, --read TEXT  Source format.
  -t, -w, --to, --write TEXT   Target format.
  -o, --output TEXT            Output path.
  --data-dir TEXT              Output directory.
  --no-pandoc                  Disable pandoc formats.
  --version                    Show the version and exit.
  --help                       Show this message and exit
```

Like `pandoc`, if no files are provided on the command line, podoc takes its input on stdin.

## Use-cases

Here are a few common use-cases enabled by podoc.

### Converting a notebook to Markdown

We download a notebook and convert it to Markdown:

![nbmd](https://cloud.githubusercontent.com/assets/1942359/14084014/098bb0c4-f519-11e5-94b1-577f4f406406.png)

### Converting a notebook to docx via pandoc

We download a notebook, we convert it to a JSON-based intermediate representation (`ast`) then to docx with pandoc:

![nbdocx](https://cloud.githubusercontent.com/assets/1942359/14084070/575b6024-f519-11e5-9ece-fe0bde1a28b4.png)

### Quickly creating a new Jupyter notebook from the command-line

We generate a notebook from stdin (we type the contents directly in the terminal, and we press `Ctrl+D` when we're done):

![stdinnb](https://cloud.githubusercontent.com/assets/1942359/14084148/ace75b7e-f519-11e5-9f67-fa92f1b1f217.png)

### Writing Markdown in the Jupyter Notebook

You can edit in the Jupyter Notebook all documents in podoc-supported formats. You just have to open a Jupyter Notebook server with the following command:

```bash
jupyter notebook --NotebookApp.contents_manager_class=podoc.notebook.PodocContentsManager
```

For example, you can edit any Markdown document in the Notebook. Code cells are automatically converted into code blocks.

## Installation

The code is changing rapidly and there is no PyPI release yet.

The main requirements are:

* Python 2.7 or 3.4+
* CommonMark
* nbformat
* click
* pandoc and pypandoc

To install the package:

```bash
$ git clone https://github.com/podoc/podoc.git
$ cd podoc
$ pip install -r requirements.txt
$ pip install -r requirements-dev.txt
$ python setup.py develop
$ make test  # you need pandoc to run the test suite
```

## Architecture overview

*This will need to be expanded in the documentation.*

* `podoc.core.Podoc` is the main class. One can register *formats* and *transformation functions* from any format to another, thus forming a **directed graph**. The `convert()` method converts a document between formats by computing a shortest path in the graph.
* Each format may register a file extension and `load(s)/dump(s)` functions to convert from an in-memory representation of the document to a file/string. For example, the `notebook` format registers JSON `load(s)/dump(s)` functions for a `Notebook` instance via the nbformat package.
* By default, a `Podoc` instance registers all pandoc formats and conversion paths, if pandoc and pypandoc are installed. You can disable this if you want to.
* The rest of the library is implemented in built-in **plugins**. A plugin is just a class deriving from `podoc.plugin.IPlugin` that is defined in a loaded Python script. The plugin attaches to a `Podoc` instance via the `attach(podoc)` method, where it can register formats/functions. All discovered plugins are automatically loaded when you instantiate a `Podoc` class, but you can also specify the list of plugins to use.
* A generic recursive tree structure is implemented in `podoc.tree`. It is based on nested dict subclasses (`Node` class). Use `node.show()` to display a nice hierarchical representation of a tree. There is also a `TreeTransformer` class where you can override `transform_XXX()` methods to transform any type of node. We use this framework to convert abstract syntax trees.
* **AST plugin**: this plugin implements an in-memory representation of any document. This representation closely follows the representation used in latest version of pandoc (1.17 at this time).

  * A document consists of a list of Block elements (`Para`, `List`, `CodeBlock`, etc.), each Block containing other Blocks, strings, or Inlines (`Emph`, `Image`, etc.). These elements can have metadata (the image's URL, for example).
  * **Custom nodes can be used by plugins; if a plugin encounters an unknown node, it just skips it and process the children recursively.** This is to keep in mind if you implement a custom format.
  * An AST can be imported/exported to a JSON document which has exactly the same format as pandoc's intermediate representation (`json` format). This is how we achieve compatibility with pandoc. Not all pandoc features are supported at this time (most notably, tables).
  * The compatibility is extensively tested in the test suite. We'll add even more tests in the future.
* **Markdown plugin**: this plugin implements transformations between AST and Markdown via the **CommonMark-py** package. podoc converts between the internal CommonMark-py AST and the podoc AST. **podoc implements no Markdown parser on its own**. We test the compatibility of the Markdown-AST transformations with pandoc's own Markdown parser (currently based on `markdown_strict` plus a few extensions).
* **Notebook plugin**: this plugin implements transformations between AST and Jupyter Notebook via the **nbformat** package.

  * To convert a notebook to Markdown, we parse every Markdown cell with the Markdown plugin, and we convert every code cell to a special `CodeCell` node. This custom AST node contains a `CodeBlock` with the source, and a list of `CodeBlock` (with `result`, `stdout`, or `stderr` "language") or `Para` (images) with the cell's outputs. Images are saved to external files and inserted in Markdown. We keep a `resources` dictionary mapping the external filenames to the data (binary string).
  * To convert a Markdown document to a notebook, we first convert it to an AST, then we loop through the top-level blocks to detect `CodeBlock` which should be wrapped within `CodeCell`s. There are a few heuristics to decide whether a `CodeBlock` is a `CodeCell` or a regular Markdown code block, and to find the list of outputs. These heuristics could certainly be improved. This logic is implemented in `podoc.notebook.wrap_code_cells()`. When converting a notebook to another podoc format (for example, HTML, although it is not yet implemented), the information about the `CodeCell`s can be used for custom styling. If the target format doesn't know about `CodeCell`s, it will just discard them and process the children recursively.
* Every plugin comes with a set of test files in its own format. We automatically test all conversion paths on all test files as part of the test suite.

## Plugin ideas

podoc features a simple plugin system that allows you to implement custom transformation functions. Here are a few plugin ideas (none is implemented yet!):

* `ASCIIImage`: replace images by ASCII art to display documents with images in the console.
* `Atlas`: filter replacing code blocks in a given language by executable `<pre>` HTML code blocks, and LaTeX equations by `<span>` HTML blocks. This is used by the O'Reilly Atlas platform.
* `CodeEval`: evaluate some code elements and replace them by their output. This allows for **literate programming** using Python.
* `Graph`: describe a graph or a tree in a human-readable format and have it converted automatically to an image (e.g. [mermaid](http://knsv.github.io/mermaid/))
* `Include`: just include several documents in a single document.
* `Macros`: perform regex substitutions. The macro substitutions can be listed in the `macros` metadata array in the document, or in `c.Macros.substitutions = [(regex, repl), ...]` in your `.podoc/podoc_config.py`.
* `Prompt`: parse and write prompt prefix in an input code cell.
* `SlideShow`: read and write slideshows
* `UrlChecker`: find all broken hypertext links and generate a report.
