# -*- coding: utf-8 -*-
# flake8: noqa

"""Installation script."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os
import os.path as op
import re

from setuptools import setup


#------------------------------------------------------------------------------
# Setup
#------------------------------------------------------------------------------

def _package_tree(pkgroot):
    path = op.dirname(__file__)
    subdirs = [op.relpath(i[0], path).replace(op.sep, '.')
               for i in os.walk(op.join(path, pkgroot))
               if '__init__.py' in i[2]]
    return subdirs


curdir = op.dirname(op.realpath(__file__))
readme = open(op.join(curdir, 'README.md')).read()


# Find version number from `__init__.py` without executing it.
filename = op.join(curdir, 'podoc/__init__.py')
with open(filename, 'r') as f:
    version = re.search(r"__version__ = '([^']+)'", f.read()).group(1)


setup(
    name='podoc',
    version=version,
    license="BSD",
    description='Markup document conversion',
    long_description=readme,
    author='Cyrille Rossant',
    author_email='cyrille.rossant at gmail.com',
    url='https://github.com/podoc/podoc/',
    packages=_package_tree('podoc'),
    package_dir={'podoc': 'podoc'},
    package_data={
    },
    entry_points={
        'console_scripts': [
            # 'podoc=podoc.scripts.podoc_script:main',
        ],
    },
    include_package_data=True,
    keywords='podoc,pandoc,markup,markdown,conversion',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Topic :: Text Processing :: Markup',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
)
