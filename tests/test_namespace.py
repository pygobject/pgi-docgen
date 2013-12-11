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

        self.assertEqual(ns.types["SOUP_STATUS_CANCELLED"],
                         "Soup.Status.CANCELLED")

        self.assertEqual(ns.types["SoupContentDecoder"],
                         "Soup.ContentDecoder")

        self.assertEqual(ns.types["SoupContentDecoder"],
                         "Soup.ContentDecoder")

        self.assertEqual(ns.types["soup_cookie_parse"],
                         "Soup.Cookie.parse")

    def test_gtk(self):
        ns = Namespace("Gtk", "3.0")

        self.assertEqual(ns.types["GtkWindow"], "Gtk.Window")
        self.assertEqual(ns.types["GtkAppChooser"], "Gtk.AppChooser")
        self.assertEqual(ns.types["GtkArrowType"], "Gtk.ArrowType")

    def test_gdk(self):
        ns = Namespace("Gdk", "3.0")

        self.assertEqual(ns.types["GdkModifierType"], "Gdk.ModifierType")

    def test_gobject(self):
        ns = Namespace("GObject", "2.0")

        self.assertEqual(ns.types["GTypeCValue"], "GObject.TypeCValue")
        self.assertEqual(ns.types["GBoxed"], "GObject.GBoxed")

    def test_glib(self):
        ns = Namespace("GLib", "2.0")

        self.assertEqual(ns.types["GBookmarkFileError"],
                         "GLib.BookmarkFileError")

    def test_cairo(self):
        ns = Namespace("cairo", "1.0")

        self.assertEqual(ns.types["cairo_t"], "cairo.Context")
