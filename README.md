# podoc

**This is a work in progress**

**podoc** is a **minimalistic pure Python pandoc clone**, i.e. a markup document conversion library. Currently, it supports the Markdown, Jupyter notebook, OpenDocument, O'Reilly Atlas, Python formats. Support for ReST, LaTeX, HTML, AsciiDoc is planned.

podoc provides a Python API as well as a command-line tool. The architecture is modular and allows for the creation of custom formats, readers, writers, preprocessors, postprocessors, and filters.

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
podoc -f xxx_format -t yyy_format file.xxx -o file.yyy
```

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
* `run.sh`: a podoc command that converts `input.xxx` into `output.yyy`

All examples are automatically checked as part of podoc's testing suite.

## Advanced documentation

### Features

* Command-line tool
* Full Python API
* Native support for Jupyter notebooks
* Fully customizable transformation pipeline
* Built-in set of preprocessors and postprocessors
* Global and block metadata
* Inline LaTeX equations
* Templates

The following features (supported by pandoc) may or may not be considered in the future:

* Bibliography
* Tables
* Markdown extensions
* Slide shows

### Architecture

podoc uses the following pipeline to convert a document:

* **Preprocessors** (optional): the input document can be processed before the conversion.
* **Reader**: the processed input document is parsed and transformed into an in-memory **Abstract Syntax Tree** (AST). The AST is fully JSON-serializable.
* **Filters** (optional): filters can transform the AST.
* **Writer**: a writer transforms the filtered AST into an output document.
* **Postprocessors** (optional): the output document can be processed after the conversion.

To use custom processors or formats, put your code in a Python script (for example, `custom.py`), and add the following line:

```python
class MyPreprocessor(Preprocessor):
    ...

...

from podoc import register
register(preprocessors=[MyPreprocessor()],
         reader='notebook',
         filters=['some_builtin_filter', MyFilter()],
         writer=MyWriter(),
         postprocessors=[MyPostprocessor1(), MyPostprocessor2()],
         )
```

Then, use the following command:

```bash
podoc --script=custom.py myfile.xxx -o myfile.yyy
```

You can override the processors defined in your script with the usual arguments `--filters`, `-t`, `-f`, and so on.

### AST

Every document is converted into a native representation called the AST (the same as in pandoc). This is a tree with a `Meta` block (containing metadata like title, authors, and date) and a list of `Block` elements. Each `Block` contains a `Meta` element and a list of `Inline` elements.

* [List of Block elements](http://hackage.haskell.org/package/pandoc-types-1.12.4.5/docs/Text-Pandoc-Definition.html#t:Block)
* [List of Inline elements](http://hackage.haskell.org/package/pandoc-types-1.12.4.5/docs/Text-Pandoc-Definition.html#t:Inline)

When converted to JSON, each element has the following fields (this corresponds to pandoc's JSON format):

* `t`: the name of the `Block` or `Inline` element
* `c`: a string, or a list of `Inline` elements


### Preprocessors

The included preprocessors are:

* `CodeEval`: evaluates code enclosed in particular markup syntax (as provided by a regular expression). This allows for **literate programming**, using Python or any other language.

To create your own preprocessor:

```python
class MyPreprocessor(Preprocessor):
    def run(self, doc):
        # hack hack hack
        return doc
```

### Readers

To create your own reader:

```python
class MyReader(Reader):
    def run(self, doc):
        # hack hack hack
        return ast
```

You can also provide directly a block and inline grammar and define your own lexer.

### Filters

The included filters are:

* `Atlas`: replace code blocks in a given language by executable `<pre>` HTML code blocks, and LaTeX equations by `<span>` HTML blocks.

To create your own filter:

```python
class MyFilter(Filter):
    def run(self, ast):
        # ast is a Python dictionary containing Block and Inline elements.
        # hack hack hack
        return ast
```

You can also choose to not override `run(ast)`, and implement `handle_code_block(element)` and similar instead. The default `run(ast)` method traverses the tree and calls the `handle_xxx(element)` methods if they exist.

### Writers

To create your own writer:

```python
class MyWriter(Writer):
    def create_output(self):
        # You can override this (for example, create a new ODT document).
        self.output = StringWriter()

    def run(self, ast):
        # hack hack hack
        # You can use self.output.append().
        return doc

    @property
    def contents(self):
        # You can override this.
        return self.output.contents
```

### Postprocessors

To create your own postprocessor:

```python
class MyPostprocessor(Postprocessor):
    def run(self, doc):
        # hack hack hack
        return doc
```
