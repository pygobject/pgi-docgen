# -*- coding: utf-8 -*-

import os
import sys

for entry in os.listdir("api"):
    path = os.path.join("api", entry)
    if os.path.isdir(path) and "_" in entry:
        sys.path.insert(0, os.path.abspath(path))

sys.path.insert(0, os.path.abspath("../../"))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    'sphinx.ext.inheritance_diagram',
]
source_suffix = '.rst'
master_doc = 'index'
project = 'pgidoc'
version = "0.1"
release = "0.1"
exclude_patterns = ['_build', 'README.rst']

intersphinx_mapping = {
    'python': ('http://docs.python.org/2.7', None),
    'cairo': ('http://cairographics.org/documentation/pycairo/2/', None),
}

html_theme_path = ['.']
html_theme = 'theme'
html_copy_source = False
html_show_sourcelink = False

inheritance_node_attrs = dict(shape='box', fontsize=7,
                              color='gray70', style='rounded')
inheritance_graph_attrs = dict(rankdir="TB", size='""', bgcolor="transparent")

autodoc_member_order = "bysource"
