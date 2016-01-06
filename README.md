# podoc

[![Build Status](https://img.shields.io/travis/podoc/podoc.svg)](https://travis-ci.org/podoc/podoc)
[![codecov.io](https://img.shields.io/codecov/c/github/podoc/podoc.svg)](http://codecov.io/github/podoc/podoc?branch=master)
[![Documentation Status](https://readthedocs.org/projects/podoc/badge/?version=latest)](https://readthedocs.org/projects/podoc/?badge=latest)
[![PyPI release](https://img.shields.io/pypi/v/podoc.svg)](https://pypi.python.org/pypi/podoc)
[![GitHub release](https://img.shields.io/github/release/podoc/podoc.svg)](https://github.com/podoc/podoc/releases/latest)
[![Join the chat at https://gitter.im/podoc/podoc](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/podoc/podoc?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

**This library is in a very early development stage and it's not ready for public use yet.**

**podoc** will be a pure Python library for converting markup documents in a way that is **100% compatible with pandoc**. You'll be able to convert documents bidirectionally between the following formats:

* **Without pandoc installed**:
  * CommonMark/Markdown
  * Jupyter Notebook
  * OpenDocument
  * O'Reilly Atlas
  * ReST (later?)
  * LaTeX (later?)
  * HTML (later?)
* **With pandoc installed**:
  * all formats above
  * the dozens of formats supported by pandoc

podoc implements no parser. Instead, it uses other parsing libraries like CommonMark-py, Jupyter, odfpy, etc.

Conversion will be entirely customizable and will allow many use-cases (see the *Plugin ideas* section below).

## Plugins

podoc implements a very light core. Most functionality is provided by built-in plugins, and you can implement your own plugins easily. Examples of included plugins are support for all natively supported formats like CommonMark, Notebook, AST, etc.

## AST

podoc features a language-independent representation for documents, also known as **Abstract Syntax Tree** (AST). This structure is very close the the internal AST used by pandoc, and podoc provides 100% compatible import/export facilities to the pandoc AST JSON format.

## Custom AST nodes

The AST supports a small set of built-in node types, like `Header`, `Para`, or `CodeBlock` (the same names as in pandoc). You can also implement your own custom node types which allow for a rich set of possibilities.

For example, the Notebook plugin implements the `CodeCell` node. Its children are the input cell as a `CodeBlock` and output cells as `CodeBlock`s.

When you define a custom node type, make sure that its children are native, such that writers that don't support the node type can still process sensible contents. This is because the default behavior for writers is to just skip unknown nodes and proceed with the children as usual, recursively. In the `CodeCell` example, you can see that the children are native `CodeBlock`s so that writers that don't support `CodeCell` will still render a list of code blocks. Writers that *do* support Notebook `CodeCell` will have a chance to render them in a specific way.

## Formats

In podoc, there is a list of formats which are nodes in a conversion (directed) graph, and a list of conversion functions which are edges in that graph. To go from one format to another, the shortest path is found and the conversion is performed. In practice, the conversion path is almost always `source -> AST -> target`, and most formats implement both readers (`source -> AST`) and writers (`AST -> target`).

Some conversion paths don't require a full AST parsing, for example `notebook -> CommonMark` (since notebooks already contain Markdown cells), which is significantly faster than `notebook -> AST -> CommonMark`.

## Filters

You can register *filters* that transform a document without changing the format. For example, prefilters that transform the source document or AST filters that implement custom features.

See a list of possible filters below.

## Plugin ideas

* `ASCIIImage`: replace images by ASCII art to display documents with images in the console.
* `Atlas`: filter replacing code blocks in a given language by executable `<pre>` HTML code blocks, and LaTeX equations by `<span>` HTML blocks. This is used by the O'Reilly Atlas platform.
* `CodeEval`: evaluate some code elements and replace them by their output. This allows for **literate programming** using Python.
* `Graph`: describe a graph or a tree in a human-readable format and have it converted automatically to an image (e.g. [mermaid](http://knsv.github.io/mermaid/))
* `Include`: just include several documents in a single document.
* `Macros`: perform regex substitutions. The macro substitutions can be listed in the `macros` metadata array in the document, or in `c.Macros.substitutions = [(regex, repl), ...]` in your `.podoc/config.py`.
* `Prompt`: parse and write prompt prefix in an input code cell.
* `SlideShow`: convert Markdown documents or Jupyter notebooks to slideshows
* `UrlChecker`: find all broken hypertext links and generate a report.
