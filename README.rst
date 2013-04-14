What is this?
=============

An experiment to create sphinx docs for gi modules using python introspection.

docgen.py introspects the gi module and pulls in the gir docs.
I creates a fake python module for each gi module that contains
the whole API.

docbuild.py builds html docs using sphinx, optimizes png sizes and packages it.

Both steps need a working (and the same) gi (no readthedocs.org etc.)


How do I get started?
---------------------

::

    ./docgen.py # Tutorial only
    ./docgen.py Gtk-3.0 Gst-1.0 # Tutorial + API docs for Gtk/Gst, needs pgi
    ./docbuild.py

`build.tar.gz` contains the generated docs


License
-------

Everything in the `tutorial` sub directory:

    GNU Free Documentation License 1.3 with no Invariant Sections, no
    Front-Cover Texts, and no Back-Cover Texts

Everything else:

    GNU Lesser General Public License 2.1 or later
