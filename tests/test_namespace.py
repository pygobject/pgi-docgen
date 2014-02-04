# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


import unittest

from pgidocgen.namespace import Namespace


class TNamespace(unittest.TestCase):

    def test_soup(self):
        ns = Namespace("Soup", "2.4")
        types = ns.get_types()

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

        self.assertEqual(types["GtkWindow"], "Gtk.Window")
        self.assertEqual(types["GtkAppChooser"], "Gtk.AppChooser")
        self.assertEqual(types["GtkArrowType"], "Gtk.ArrowType")

    def test_gdk(self):
        ns = Namespace("Gdk", "3.0")
        types = ns.get_types()

        self.assertEqual(types["GdkModifierType"], "Gdk.ModifierType")

    def test_gobject(self):
        ns = Namespace("GObject", "2.0")
        types = ns.get_types()

        self.assertEqual(types["GTypeCValue"], "GObject.TypeCValue")
        self.assertEqual(types["GBoxed"], "GObject.GBoxed")

        self.assertEqual(types["G_MAXSSIZE"], "GObject.G_MAXSSIZE")

    def test_glib(self):
        ns = Namespace("GLib", "2.0")
        types = ns.get_types()

        self.assertEqual(types["GBookmarkFileError"],
                         "GLib.BookmarkFileError")

        self.assertEqual(types["G_MININT8"], "GLib.MININT8")

    def test_cairo(self):
        ns = Namespace("cairo", "1.0")
        types = ns.get_types()

        self.assertEqual(types["cairo_t"], "cairo.Context")

    def test_pango(self):
        ns = Namespace("Pango", "1.0")
        types = ns.get_types()

        self.assertEqual(types["pango_break"], "Pango.break_")
