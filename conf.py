# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.abspath('./_generated'))
import gi

extensions = ['sphinx.ext.autodoc']
source_suffix = '.rst'
master_doc = 'index'
project = 'pgidoc'
copyright = u'2013, Christoph Reiter'
version = "0.1"
release = "0.1"
exclude_patterns = ['_build', 'README.rst']

html_theme_path = ['.']
html_theme = 'minimalism'
