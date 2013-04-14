#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

fake_gtk_main = """
def fake_gtk_main(path):
    from gi.repository import Gtk
    import cairo

    window = Gtk.Window.list_toplevels()[0]
    window.set_border_width(6)

    while Gtk.events_pending():
        Gtk.main_iteration_do(True)

    # increase until errors are gone... :/
    for x in xrange(5000):
        Gtk.main_iteration_do(False)

    alloc = window.get_allocation()
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, alloc.width, alloc.height)
    context = cairo.Context(surface)
    window.draw(context)
    surface.write_to_png(path)

    for x in Gtk.Window.list_toplevels():
        x.destroy()

    while Gtk.Window.list_toplevels():
        Gtk.main_iteration_do(False)
"""

if __name__ == "__main__":
    for entry in os.listdir("examples"):
        if not entry.endswith(".py"):
            continue
        path = os.path.join("examples", entry)
        h = open(path, "rb")
        data = h.read()
        h.close()
        assert "Gtk.main" in data
        name = os.path.splitext(entry)[0]
        data = fake_gtk_main + data
        try:
            os.mkdir("screenshots")
        except:
            pass
        dest_path = os.path.join("..", "screenshots", name + ".png")
        data = data.replace("Gtk.main()", "fake_gtk_main('%s')" % dest_path)
        def x():
            os.chdir("examples")
            exec data in {}
            os.chdir("..")
        x()
