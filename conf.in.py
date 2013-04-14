# -*- coding: utf-8 -*-

import os
import sys

has_api = False
if os.path.exists("api"):
    for entry in os.listdir("api"):
        path = os.path.join("api", entry)
        if os.path.isdir(path) and "_" in entry:
            sys.path.insert(0, os.path.abspath(path))
            has_api = True

sys.path.insert(0, os.path.abspath(".."))

try:
    import pgi
except ImportError:
    if has_api:
        raise
else:
    pgi.install_as_gi()

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    'sphinx.ext.inheritance_diagram',
]
source_suffix = '.rst'
master_doc = 'index'
project = 'pgi-docs'
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
html_title = "PGI Documentation"
html_short_title = "Main"

inheritance_node_attrs = dict(shape='box', fontsize=7,
                              color='gray70', style='rounded')
inheritance_graph_attrs = dict(rankdir="TB", size='""', bgcolor="transparent")

autodoc_member_order = "bysource"
