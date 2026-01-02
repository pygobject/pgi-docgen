.. image:: https://codecov.io/gh/pygobject/pgi-docgen/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/pygobject/pgi-docgen

What is this?
=============

A tool to create Sphinx documentation for GI modules using Python
introspection.

``pgi-docgen create`` introspects the GI module, pulls in the GIR docs and
creates a Sphinx environment.

``pgi-docgen build`` builds HTML documentation using Sphinx.

How do I get started?
---------------------

::

    # API docs for Gtk/Gst:
    uv run ./tools/build.sh Gtk-3.0 Gst-1.0

The resulting docs can be found in ``_docs/_build``


How do I build docs for private libraries?
------------------------------------------

The following creates docs for the in gnome-music included libgd::

    XDG_DATA_DIRS=$XDG_DATA_DIRS:/usr/share/gnome-music/ \
    GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/gnome-music/girepository-1.0/ \
    LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/gnome-music/ ./build.sh Gd-1.0


Intersphinx
-----------

There are two ways to reference the online API reference from sphinx
generated documentation:

1) Including the sidebar (needs JavaScript)

   ::

        intersphinx_mapping = {
            'gtk': ('https://lazka.github.io/pgi-docs/#Gtk-3.0/',
                    'https://lazka.github.io/pgi-docs/Gtk-3.0/objects.inv'),
        }

2) Without the sidebar

   ::

        intersphinx_mapping = {
            'gtk': ('https://lazka.github.io/pgi-docs/Gtk-3.0', None),
        }


Licenses
--------

Everything in the ``pgidocgen/gen/data/theme`` sub directory:

    https://github.com/rtfd/readthedocs.org

    MIT License

Fonts in ``pgidocgen/gen/data/theme/static/fonts``

    Lato:
        https://www.latofonts.com

        SIL Open Font License 1.1

    DejaVu Sans Mono:
        https://dejavu-fonts.github.io/

        Public Domain

    FontAwesome:
        https://fontawesome.io

        SIL OFL 1.1

``pgidocgen/gen/data/ext/devhelp_fork.py``

    https://bitbucket.org/birkenfeld/sphinx/

    BSD

``pgidocgen/gen/data/index/jquery-2.2.0.min.js``

    https://jquery.org/

    MIT License

Everything else:

    GNU Lesser General Public License 2.1 or later
