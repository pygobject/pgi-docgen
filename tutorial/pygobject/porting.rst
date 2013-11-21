Porting PyGTK code
==================

Using the PyGTK compatibility module
------------------------------------

::

    from gi import pygtkcompat

    pygtkcompat.enable() 
    pygtkcompat.enable_gtk(version='3.0')

Automatic renaming/replacing of PyGTK code
------------------------------------------

https://git.gnome.org/browse/pygobject/tree/pygi-convert.sh

Default Encoding
----------------

PyGTK swiched the default encoding to utf-8 on import. This is not the case 
anymore with PyGObject, so any code depending on it might break.

To get the old behavior you have to reload the sys module and change
the default encoding.

::

    reload(sys)
    sys.setdefaultencoding("utf-8")

While setting the default encoding restores the old behavior, it
is good practice to not depend on the default encoding at all.
