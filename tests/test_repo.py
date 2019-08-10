# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


import unittest

from pgidocgen.repo import Repository
from pgidocgen.docobj import Class, Function, Flags, get_hierarchy, PyClass, \
    Constant
from pgidocgen.overrides import parse_override_docs


def find(l, name):
    for i in l:
        if i.name == name:
            return i
    raise LookupError


class TRepository(unittest.TestCase):

    def test_parse_override_docs(self):
        docs = parse_override_docs("Gtk", "3.0")
        self.assertTrue("Gtk.Widget.translate_coordinates" in docs)
        self.assertTrue(docs["Gtk.Widget.translate_coordinates"])

    def test_override_method(self):
        repo = Repository("Gtk", "3.0")
        Gtk = repo.import_module()
        func = Function.from_object(
            "Gtk.Widget", "translate_coordinates", Gtk.Widget.translate_coordinates, repo, Gtk.Widget)
        self.assertEqual(func.signature, "(dest_widget, src_x, src_y)")

    def test_method_inheritance(self):
        repo = Repository("Atk", "1.0")
        Atk = repo.import_module()
        klass = Class.from_object(repo, Atk.Plug)
        self.assertEqual(
            [x[0] for x in klass.methods_inherited],
            ['Atk.Object', 'GObject.Object', 'Atk.Component']
        )

    def test_hierarchy(self):
        from pgi.repository import GObject

        repo = Repository("Atk", "1.0")
        Atk = repo.import_module()
        hier = get_hierarchy([Atk.NoOpObjectFactory])
        self.assertEqual(list(hier.keys()), [GObject.Object])
        self.assertEqual(list(hier[GObject.Object].keys()),
                         [Atk.ObjectFactory])
        self.assertEqual(list(hier[GObject.Object][Atk.ObjectFactory].keys()),
                         [Atk.NoOpObjectFactory])
        self.assertFalse(
            hier[GObject.Object][Atk.ObjectFactory][Atk.NoOpObjectFactory])

    def test_pango(self):
        repo = Repository("Pango", "1.0")
        mod = repo.parse()
        func = find(mod.functions, "extents_to_pixels")
        self.assertTrue(":param inclusive:" in func.signature_desc)

        func = find(mod.functions, "break_")
        self.assertTrue(":param text:" in func.signature_desc)

        func = find(find(mod.structures, "TabArray").methods, "new")
        self.assertTrue(":param initial_size:" in func.signature_desc)

        self.assertTrue(repo.is_private("Pango.RendererPrivate"))
        self.assertFalse(repo.is_private("Pango.AttrIterator"))

    def test_glib(self):
        repo = Repository("GLib", "2.0")
        mod = repo.parse()

        klass = find(mod.pyclasses, "Error")

        # GLib.io_add_watch points to g_io_add_watch_full and should
        # also use its docs
        func = find(mod.functions, "io_add_watch")
        self.assertTrue(":param priority:" in func.signature_desc)

        # we include a note containing the shadowed docs
        self.assertTrue(func.info.shadowed_desc)

        self.assertEqual(repo.get_shadowed("g_idle_add"), "g_idle_add_full")

        self.assertEqual(repo.lookup_py_id("g_idle_add"), "GLib.idle_add")
        self.assertEqual(repo.lookup_py_id("g_idle_add", shadowed=False), None)

        klass = find(mod.enums, "BookmarkFileError")
        self.assertEqual(klass.base, "GLib.Enum")

        klass = find(mod.enums, "Enum")
        self.assertEqual(klass.base, None)

        klass = find(mod.flags, "FileTest")
        self.assertEqual(klass.base, "GLib.Flags")

        klass = find(mod.flags, "Flags")
        self.assertEqual(klass.base, None)

        struct = find(mod.structures, "MemVTable")
        field = find(struct.fields, "realloc")
        self.assertTrue("object" in field.type_desc)

    def test_gio(self):
        repo = Repository("Gio", "2.0")
        Gio = repo.import_module()

        klass = Class.from_object(repo, Gio.Application)
        method = find(klass.methods, "activate")
        signal = find(klass.signals, "activate")

        self.assertTrue(method.info.desc)
        self.assertTrue(signal.info.desc)
        self.assertNotEqual(method.info.desc, signal.info.desc)

        signal = find(klass.signals, "command_line")
        self.assertTrue(":param command_line:" in signal.signature_desc)

        klass = Class.from_object(repo, Gio.File)
        method = find(klass.methods, "load_contents_finish")
        self.assertTrue(":returns:" in method.signature_desc)

    def test_gtk_overrides(self):
        repo = Repository("Gtk", "3.0")
        Gtk = repo.import_module()

        PyClass.from_object(repo, Gtk.TreeModelRow)
        PyClass.from_object(repo, Gtk.TreeModelRowIter)

        func = Function.from_object("Gtk.Container", "child_get", Gtk.Container.child_get, repo, Gtk.Container)
        self.assertEqual(func.info.desc, "Returns a list of child property values for the given names.")
        self.assertEqual(func.signature, "(child, *prop_names)")

        func = Function.from_object("Gtk", "stock_lookup", Gtk.stock_lookup, repo, Gtk)
        self.assertEqual(func.signature, "(stock_id)")

        klass = Class.from_object(repo, Gtk.Widget)
        self.assertEqual(
            klass.subclasses.count("Gtk.Container"), 1)

    def test_gtk(self):
        repo = Repository("Gtk", "3.0")
        Gtk = repo.import_module()

        klass = Class.from_object(repo, Gtk.TreeModel)
        vfunc = find(klass.vfuncs, "do_get_iter")
        self.assertTrue(vfunc.info.desc)

        Class.from_object(repo, Gtk.Button)
        Class.from_object(repo, Gtk.Paned)
        Class.from_object(repo, Gtk.ActionBar)

        klass = Class.from_object(repo, Gtk.TextView)
        self.assertTrue(klass.image_path)

        klass = Class.from_object(repo, Gtk.Widget)
        translate_coordinates = find(klass.methods, "translate_coordinates")
        # make sure we replace src_widget with self
        self.assertTrue("src_widget" not in translate_coordinates.info.desc)

        mod = repo.parse()
        find(mod.class_structures, "WidgetClass")
        find(mod.structures, "TableChild")
        self.assertRaises(
            LookupError, find, mod.class_structures, "TableChild")
        self.assertRaises(
            LookupError, find, mod.structures, "WidgetClass")

    def test_gobject(self):
        repo = Repository("GObject", "2.0")
        GObject = repo.import_module()
        mod = repo.parse()

        self.assertEqual(
            repo.lookup_py_id_for_type_struct("GObjectClass"),
            "GObject.Object")

        klass = Class.from_object(repo, GObject.Object)
        method = find(klass.methods, "list_properties")
        self.assertTrue(method.is_static)
        self.assertEqual(method.fullname, "GObject.Object.list_properties")

        klass = find(mod.enums, "GEnum")
        self.assertEqual(klass.base, "GLib.Enum")

        klass = find(mod.flags, "GFlags")
        self.assertEqual(klass.base, "GLib.Flags")

        klass = find(mod.flags, "ParamFlags")
        self.assertEqual(klass.base, "GLib.Flags")

    def test_atk(self):
        repo = Repository("Atk", "1.0")
        Atk = repo.import_module()

        c = Constant.from_object(repo, "", "FOO", Atk.Document.__gtype__)
        self.assertEqual(str(c.value), "<GType AtkDocument>")

        klass = Class.from_object(repo, Atk.Document)
        method = find(klass.methods, "get_attributes")
        self.assertEqual(method.info.version_added, "1.12")

        method = find(klass.methods, "get_attribute_value")
        self.assertEqual(method.info.version_added, "1.12")

        klass = Class.from_object(repo, Atk.Hyperlink)

        method = find(klass.methods, "is_selected_link")
        self.assertTrue(method.info.deprecated)
        self.assertEqual(method.info.version_added, "1.4")
        self.assertEqual(method.info.version_deprecated, "1.8")
        self.assertTrue(method.info.deprecation_desc, "1.8")

        klass = Flags.from_object(repo, Atk.Role)
        info = find(klass.values, "APPLICATION").info
        self.assertEqual(info.version_added, "1.1.4")

    def test_gudev(self):
        repo = Repository("GUdev", "1.0")
        GUdev = repo.import_module()
        Class.from_object(repo, GUdev.Client)
