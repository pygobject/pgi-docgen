Importing modules
=================

Importing a module is as simple as

::

    from gi.repository import Gtk

It is good practice to set the required version before the first import of
a module. If no version prior to import is set the newest library will be
loaded. Since the newer version might not be compatible with your code this
could break your application depending on which libraries the user has
installed.

The first import of a module in your application should look like this:

::

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

Related Functions
-----------------

.. autofunction:: gi.require_version

.. autofunction:: gi.get_required_version

.. autofunction:: gi.check_version
