# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


import unittest

from pgidocgen.namespace import Namespace, get_cairo_types


class TNamespace(unittest.TestCase):

    def test_soup(self):
        ns = Namespace("Soup", "2.4")
        types = ns.get_types()
        ns.parse_docs()

        self.assertEqual(types["SOUP_STATUS_CANCELLED"],
                         "Soup.Status.CANCELLED")

        self.assertEqual(types["SoupContentDecoder"],
                         "Soup.ContentDecoder")

        self.assertEqual(types["SoupContentDecoder"],
                         "Soup.ContentDecoder")

        self.assertEqual(types["soup_cookie_parse"],
                         "Soup.Cookie.parse")

    def test_gtk(self):
        ns = Namespace("Gtk", "3.0")
        types = ns.get_types()
        ns.parse_docs()

        self.assertEqual(types["GtkWindow"], "Gtk.Window")
        self.assertEqual(types["GtkAppChooser"], "Gtk.AppChooser")
        self.assertEqual(types["GtkArrowType"], "Gtk.ArrowType")

    def test_gdk(self):
        ns = Namespace("Gdk", "3.0")
        types = ns.get_types()
        ns.parse_docs()

        self.assertEqual(types["GdkModifierType"], "Gdk.ModifierType")

    def test_gobject(self):
        ns = Namespace("GObject", "2.0")
        types = ns.get_types()
        ns.parse_docs()

        self.assertEqual(types["GTypeCValue"], "GObject.TypeCValue")
        self.assertEqual(types["GBoxed"], "GObject.GBoxed")

        self.assertEqual(types["G_MAXSSIZE"], "GObject.G_MAXSSIZE")

    def test_glib(self):
        ns = Namespace("GLib", "2.0")
        types = ns.get_types()
        ns.parse_docs()

        self.assertEqual(types["GBookmarkFileError"],
                         "GLib.BookmarkFileError")

        self.assertEqual(types["G_MININT8"], "GLib.MININT8")

    def test_cairo(self):
        ns = Namespace("cairo", "1.0")
        types = ns.get_types()
        ns.parse_docs()

        self.assertEqual(types["cairo_t"], "cairo.Context")

    def test_pycairo(self):
        types = get_cairo_types()
        self.assertEqual(
            types["cairo_set_operator"], "cairo.Context.set_operator")

        self.assertEqual(
            types["cairo_surface_get_content"], "cairo.Surface.get_content")

    def test_pango(self):
        ns = Namespace("Pango", "1.0")
        types = ns.get_types()
        ns.parse_docs()

        self.assertEqual(types["pango_break"], "Pango.break_")

    def test_tracker(self):
        ns = Namespace("Tracker", "0.16")
        ns.get_types()
        ns.parse_docs()
