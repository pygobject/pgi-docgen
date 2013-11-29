What is this?
=============

An experiment to create sphinx docs for gi modules using python introspection.

pgi-docgen.py introspects the gi module and pulls in the gir docs. I 
creates a fake python module for each gi module that contains the whole API
and uses the real module where needed.

pgi-docgen-build.py builds html docs using sphinx and optimizes pngs.

Both steps need a working (and the same) pgi.


How do I get started?
---------------------

::

    # Tutorial only:
    ./pgi-docgen.py -t <some_path>
    # Tutorial + API docs for Gtk/Gst:
    ./pgi-docgen.py -t <some_path> Gtk-3.0
    # Finally create the docs in <dest_path>
    ./pgi-docgen-build.py <dest_path> <some_path>


License
-------

Everything in the `tutorial` sub directory:

    https://github.com/sebp/PyGObject-Tutorial

    GNU Free Documentation License 1.3 with no Invariant Sections, no
    Front-Cover Texts, and no Back-Cover Texts

Everything in the `data/theme` sub directory:

    https://github.com/rtfd/readthedocs.org

    MIT License

Everything in the `data/ext` sub directory:

    https://bitbucket.org/birkenfeld/sphinx/

    BSD

Everything else:

    GNU Lesser General Public License 2.1 or later
