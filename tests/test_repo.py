# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


import unittest

from pgidocgen.repo import Repository, Class, get_hierarchy
from pgidocgen import util


def find(l, name):
    for i in l:
        if i.name == name:
            return i
    raise LookupError


class TRepository(unittest.TestCase):

    def test_hierarchy(self):
        from pgi.repository import GObject

        repo = Repository("Atk", "1.0")
        Atk = repo.import_module()
        hier = get_hierarchy([Atk.NoOpObjectFactory])
        self.assertEqual(hier.keys(), [GObject.Object])
        self.assertEqual(hier[GObject.Object].keys(), [Atk.ObjectFactory])
        self.assertEqual(hier[GObject.Object][Atk.ObjectFactory].keys(),
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
        self.assertTrue(":param initial\\_size:" in func.signature_desc)

        self.assertTrue(repo.is_private("Pango.RendererPrivate"))
        self.assertFalse(repo.is_private("Pango.AttrIterator"))

    def test_glib(self):
        repo = Repository("GLib", "2.0")
        mod = repo.parse()

        # GLib.io_add_watch points to g_io_add_watch_full and should
        # also use its docs
        func = find(mod.functions, "io_add_watch")
        self.assertTrue(":param priority:" in func.signature_desc)

        # we include a note containing the shadowed docs
        self.assertTrue(func.info.shadowed_desc)

        klass = find(mod.structures, "IConv")
        func = find(klass.methods, "_")
        self.assertTrue(func.info.desc)

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
        self.assertTrue(":param command\\_line:" in signal.signature_desc)

        klass = Class.from_object(repo, Gio.File)
        method = find(klass.methods, "load_contents_finish")
        self.assertTrue(":returns:" in method.signature_desc)

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

    def test_gobject(self):
        Repository("GObject", "2.0")

    def test_atk(self):
        repo = Repository("Atk", "1.0")
        Atk = repo.import_module()

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

    def test_gudev(self):
        repo = Repository("GUdev", "1.0")
        GUdev = repo.import_module()
        Class.from_object(repo, GUdev.Client)
