What is this?
=============

An experiment to create sphinx docs for gi modules using python introspection.

pgi-docgen.py introspects the gi module and pulls in the gir docs. I 
creates a fake python module for each gi module that contains the whole API
and uses the real module where needed.

pgi-docgen-build.py builds html docs using sphinx and optimizes pngs.

Both steps need a working (and the same) pgi.


Requirements
------------

* Python2.7 or PyPy
* pgi (trunk)
* Sphinx
* BeautifulSoup 3
* graphviz

Calling ``source bootstrap.sh`` will put you in a virtualenv with all 
dependencies installed (except graphviz).


How do I get started?
---------------------

::

    # API docs for Gtk/Gst:
    ./build.sh Gtk-3.0 Gst-1.0

    # Create docs for all (working) packages in Debian Jessie
    # Warning: This can take about an hour.
    ./build_all.sh

The resulting docs can be found in ``_docs/_build``


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


License
-------

Everything in the ``data/theme`` sub directory:

    https://github.com/rtfd/readthedocs.org

    MIT License

``data/theme/static/js/modernizr.min.js``:

    http://modernizr.com

    MIT License

``data/theme/static/fonts/lato*.wof``

    http://www.latofonts.com

    SIL Open Font License

Everything in the ``data/ext`` sub directory:

    https://bitbucket.org/birkenfeld/sphinx/

    BSD

Everything else:

    GNU Lesser General Public License 2.1 or later
