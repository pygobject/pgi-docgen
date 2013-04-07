#!/bin/sh
./docgen.py GLib-2.0 GObject-2.0 cairo-1.0 Pango-1.0 PangoCairo-1.0 Gio-2.0 Gdk-3.0 GdkPixbuf-2.0 Gtk-3.0  Gst-1.0 Clutter-1.0 Cogl-1.0
./docbuild.py
