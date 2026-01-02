# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


import unittest

from pgidocgen.namespace import get_cairo_types, \
    fixup_since, get_versions, get_namespace


class TNamespace(unittest.TestCase):

    def test_soup(self):
        ns = get_namespace("Soup", "3.0")
        types = ns.types
        ns.docs

        self.assertEqual(types["SOUP_STATUS_CANCELLED"],
                         ["Soup.Status.CANCELLED"])

        self.assertEqual(types["SoupContentDecoder"],
                         ["Soup.ContentDecoder"])

        self.assertEqual(types["SoupContentDecoder"],
                         ["Soup.ContentDecoder"])

        self.assertEqual(types["soup_cookie_parse"],
                         [u'Soup.Cookie.parse', u'Soup.cookie_parse'])

    def test_gtk(self):
        ns = get_namespace("Gtk", "3.0")
        types = ns.types
        ns.docs

        for key, values in types.items():
            for v in values:
                self.assertTrue(v.startswith("Gtk."), msg=v)

        self.assertEqual(types["GtkWindow"], ["Gtk.Window"])
        self.assertEqual(types["GtkAppChooser"], ["Gtk.AppChooser"])
        self.assertEqual(types["GtkArrowType"], ["Gtk.ArrowType"])

        type_structs = ns.type_structs
        self.assertEqual(type_structs["GtkTreeStoreClass"], "Gtk.TreeStore")

        self.assertEqual(types["gtk_list_store_newv"], ["Gtk.ListStore.new"])
        self.assertEqual(types["gtk_list_store_new"], [])

    def test_gdk(self):
        ns = get_namespace("Gdk", "3.0")
        types = ns.types
        docs = ns.docs
        versions = get_versions(docs)
        self.assertTrue("2.0" in versions)
        self.assertTrue("3.0" in versions)

        self.assertEqual(types["GdkModifierType"], ["Gdk.ModifierType"])
        self.assertEqual(
            ns.instance_params["Gdk.Window.begin_paint_region"], "window")

    def test_gdkpixbuf(self):
        ns = get_namespace("GdkPixbuf", "2.0")

        self.assertEqual(ns.types["gdk_pixbuf_animation_ref"], [])

    def test_gobject(self):
        ns = get_namespace("GObject", "2.0")
        types = ns.types
        ns.docs

        self.assertEqual(types["GTypeCValue"], ["GObject.TypeCValue"])
        self.assertEqual(types["GBoxed"], ["GObject.GBoxed"])

        self.assertEqual(types["G_MAXSSIZE"], ["GObject.G_MAXSSIZE"])
        self.assertEqual(types["GType"], ["GObject.GType"])

    def test_glib(self):
        ns = get_namespace("GLib", "2.0")
        types = ns.types
        ns.docs

        self.assertEqual(types["GBookmarkFileError"],
                         ["GLib.BookmarkFileError"])

        self.assertEqual(types["G_MININT8"], ["GLib.MININT8"])

        self.assertEqual(types["g_idle_add_full"], ["GLib.idle_add"])

        # non-introspectable
        self.assertEqual(ns.types["GVariantIter"], [])

    def test_atk(self):
        ns = get_namespace("Atk", "1.0")
        ns.types
        docs = ns.docs
        versions = get_versions(docs)
        self.assertTrue("ATK-0.7" not in versions)
        self.assertTrue("0.7" in versions)
        self.assertTrue("2.16" in versions)

    def test_cairo(self):
        ns = get_namespace("cairo", "1.0")
        types = ns.types
        ns.docs

        self.assertEqual(types["cairo_t"], ["cairo.Context"])

    def test_pycairo(self):
        types = get_cairo_types()
        self.assertEqual(
            types["cairo_set_operator"], ["cairo.Context.set_operator"])

        self.assertEqual(
            types["cairo_surface_get_content"], ["cairo.Surface.get_content"])

    def test_pango(self):
        ns = get_namespace("Pango", "1.0")
        types = ns.types
        ns.docs

        self.assertEqual(types["pango_break"], ["Pango.break_"])

    def test_ges(self):
        ns = get_namespace("GES", "1.0")
        ns.docs
        types = ns.types
        self.assertTrue("position" not in types)

    def test_deps(self):
        ns = get_namespace("DBus", "1.0")
        deps = ns.dependencies
        self.assertTrue(("GObject", "2.0") in deps)

        ns = get_namespace("GLib", "2.0")
        deps = ns.dependencies
        self.assertFalse(deps)

        ns = get_namespace("GObject", "2.0")
        deps = ns.dependencies
        self.assertEqual(deps, [("GLib", "2.0")])

    def test_all_deps(self):
        ns = get_namespace("DBus", "1.0")
        deps = ns.all_dependencies
        self.assertTrue(("GObject", "2.0") in deps)
        self.assertTrue(("GLib", "2.0") in deps)

    def test_fixup_added_since(self):
        self.assertEqual(
            fixup_since("Foo\nSince: 3.14"), ("Foo", "3.14"))
        self.assertEqual(
            fixup_since("Foo\n(Since: 3.14)"), ("Foo", "3.14"))
        self.assertEqual(
            fixup_since("Foo\n@Since: ATK-3.14"), ("Foo", "3.14"))
        self.assertEqual(
            fixup_since("to the baseline. Since 3.10."),
            ("to the baseline.", "3.10"))

    def test_fixup_deprecated_since(self):
        self.assertEqual(
            fixup_since("Since 2.12. Use atk_component_get_extents()."),
            ("Use atk_component_get_extents().", "2.12"))
