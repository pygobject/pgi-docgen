.. image:: https://circleci.com/gh/pygobject/pgi-docgen.svg?style=svg
    :target: https://circleci.com/gh/pygobject/pgi-docgen

.. image:: https://codecov.io/gh/pygobject/pgi-docgen/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/pygobject/pgi-docgen


What is this?
=============

A tool to create sphinx documentation for gi modules using python
introspection.

``pgidocgen.py create`` introspects the gi module, pulls in the gir docs and
creates a sphinx environment.

``pgidocgen.py build`` builds html docs using sphinx.

Requirements
------------

* Python 3
* pgi (trunk)
* jinja2
* Sphinx
* BeautifulSoup4
* graphviz

Calling ``source ./tools/bootstrap.sh`` will put you in a
virtualenv with all dependencies installed (except graphviz).


How do I get started?
---------------------

::

    # API docs for Gtk/Gst:
    ./tools/build.sh Gtk-3.0 Gst-1.0

    # Create docs for all (working) packages in Debian Jessie
    # Warning: This can take about an hour.
    ./tools/build-debian.py

The resulting docs can be found in ``_docs/_build``


How do I build docs for private libraries?
------------------------------------------

The following creates docs for the libgd bundled and included in gnome-music::

    XDG_DATA_DIRS=$XDG_DATA_DIRS:/usr/share/gnome-music/ \
    GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/gnome-music/girepository-1.0/ \
    LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/gnome-music/ ./tools/build.sh Gd-1.0

Explanations:

1) ``$XDG_DATA_DIR/gir-1.0`` (not ``$XDG_DATA_DIR``!) contains ``Gd-1.0.gir``.

2) ``$GI_TYPELIB_PATH`` contains ``Gd-1.0.typelib``.

3) ``$LD_LIBRARY_PATH`` contains ``libgd.so``.

Another example. For the case of HarfBuzz freshly built from source,
``HarfBuzz-0.0.gir``, ``HarfBuzz-0.0.typelib`` are both inside a ``src``
sub-directory in the HarfBuzz source tree, while ``libharfbuzz.so``
is in a ``src/.libs`` sub-directory. So you need to create a directory
``gir-1.0`` further inside, copy ``HarfBuzz-0.0.gir`` over there, and set
``$XDG_DATA_DIR`` to the **parent directory** of your newly created ``gir-1.0``,
``$GI_TYPELIB_PATH`` to ``src``, and ``$LD_LIBRARY_PATH`` to ``src/.libs``.


Intersphinx
-----------

There are two ways to reference the online API reference from sphinx
generated documentation:

1) Including the sidebar (needs JavaScript)

   ::

        intersphinx_mapping = {
            'gtk': ('http://lazka.github.io/pgi-docs/#Gtk-3.0/',
                    'http://lazka.github.io/pgi-docs/Gtk-3.0/objects.inv'),
        }

2) Without the sidebar

   ::

        intersphinx_mapping = {
            'gtk': ('http://lazka.github.io/pgi-docs/Gtk-3.0', None),
        }


Licenses
--------

Everything in the ``pgidocgen/gen/data/theme`` sub directory:

    https://github.com/rtfd/readthedocs.org

    MIT License

Fonts embedded in ``pgidocgen/gen/data/theme/static/css/pgi.css``

    Lato:
        http://www.latofonts.com

        SIL Open Font License 1.1

    DejaVu Sans Mono:
        https://dejavu-fonts.github.io/

        Public Domain

    FontAwesome:
        http://fontawesome.io

        SIL OFL 1.1

``pgidocgen/gen/data/ext/devhelp_fork.py``

    https://bitbucket.org/birkenfeld/sphinx/

    BSD

``pgidocgen/gen/data/index/jquery-2.2.0.min.js``

    https://jquery.org/

    MIT License

``pgidocgen/gen/data/index/js.cookie-2.1.0.min.js``

    https://github.com/js-cookie/js-cookie

    MIT License

Everything else:

    GNU Lesser General Public License 2.1 or later
