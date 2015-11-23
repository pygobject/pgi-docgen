# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.getcwd())

from conf_data import DEPS, SOURCEURLS

TARGET = os.environ["PGIDOCGEN_TARGET_BASE_PATH"]
TARGET_PREFIX = os.environ.get("PGIDOCGEN_TARGET_PREFIX", "")
mname, mversion = os.path.basename(os.getcwd()).split("-", 1)

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.linkcode',
    '_ext.inheritance_graph',
    '_ext.devhelp_fork',
    '_ext.current_path',
]
source_suffix = '.rst'
master_doc = 'index'
version = mversion
release = mversion
exclude_patterns = ['_build', 'README.rst']

intersphinx_mapping = {
    "python": ('http://docs.python.org/2.7',
               "../_intersphinx/python.inv"),
}

for dep_name in DEPS:
    intersph_name = dep_name.replace("-", "").replace(".", "")
    if dep_name == "cairo-1.0":
        intersphinx_mapping[intersph_name] = (
            "http://cairographics.org/documentation/pycairo/2/",
            "../_intersphinx/cairo.inv")
        continue

    dep_name = TARGET_PREFIX + dep_name
    dep = os.path.relpath(os.path.join(TARGET, dep_name))
    inv = os.path.join(dep, "objects.inv")
    if not os.path.exists(inv):
        raise SystemExit("Dependency %r not found" % dep)
    intersphinx_mapping[intersph_name] = (
        os.path.join("..", "..", "..", dep_name), inv)

html_theme_path = ['.']
html_theme = '_theme'
html_copy_source = False
html_show_sourcelink = False
html_short_title = project = '%s %s' % (mname, mversion)
html_title = "%s Python API Docs" % html_short_title
html_context = {
    "extra_css_files": ["_static/css/pgi.css"],
}

def linkcode_resolve(domain, info):
    """for sphinx.ext.linkcode"""

    name = info["module"]
    if name:
        name += "."
    name += info["fullname"]
    return SOURCEURLS.get(name)
