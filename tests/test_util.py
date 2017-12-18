# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import unittest

from pgidocgen.util import is_staticmethod, \
    is_method_owner, is_fundamental, is_object, instance_to_rest, \
    get_child_properties, fake_subclasses, get_style_properties, \
    unescape_parameter, fake_bases, is_attribute_owner, unindent, \
    get_csv_line, get_signature_string
from pgidocgen.compat import long_, PY2


class TUtil(unittest.TestCase):

    def test_get_signature_string(self):
        from pgi.repository import GLib

        func = GLib.Error.__init__
        if PY2:
            assert get_signature_string(func) == "()"
        else:
            assert get_signature_string(func) == "(*args, **kwargs)"

    def test_get_csv_line(self):
        assert get_csv_line(["foo"]) == '"foo"'
        assert get_csv_line(["foo", "bla\n"]) == '"foo","bla "'
        assert get_csv_line([u"ä"]) == u'"ä"'

    def test_unindent(self):
        self.assertEqual(unindent("foo bar.", True), "foo bar.")
        self.assertEqual(unindent("foo bar.", False), "foo bar.")

    def test_method_checks(self):
        from pgi.repository import GLib

        assert not is_staticmethod(GLib.AsyncQueue, "push")
        assert is_staticmethod(GLib.Date, "new")
        assert is_staticmethod(GLib.IOChannel, "new_file")
        assert is_staticmethod(GLib.IOChannel, "new_file")
        assert is_staticmethod(GLib.Variant, "split_signature")

    def test_is_method_owner(self):
        from pgi.repository import Gtk, GLib

        assert not is_method_owner(GLib.IOError, "from_bytes")

        self.assertTrue(is_method_owner(Gtk.ActionGroup, "add_actions"))
        self.assertFalse(is_method_owner(Gtk.Range, "get_has_tooltip"))
        if os.name != "nt":
            self.assertTrue(is_method_owner(Gtk.Plug, "new"))
        self.assertTrue(is_method_owner(Gtk.Viewport, "get_vadjustment"))
        self.assertTrue(is_method_owner(Gtk.AccelGroup, "connect"))
        self.assertFalse(is_method_owner(Gtk.AboutDialog, "get_focus_on_map"))

    def test_is_attribute_owner(self):
        from pgi.repository import GdkPixbuf

        getattr(GdkPixbuf.PixbufAnimation, "ref")
        self.assertFalse(
            is_attribute_owner(GdkPixbuf.PixbufAnimation, "ref"))

    def test_class_checks(self):
        from pgi.repository import GObject, GLib

        self.assertFalse(is_fundamental(GLib.Error))
        self.assertTrue(is_fundamental(GObject.Object))
        self.assertTrue(is_fundamental(GObject.ParamSpec))
        self.assertFalse(is_fundamental(object))

    def test_is_object(self):
        from pgi.repository import Gtk

        self.assertTrue(is_object(Gtk.Button))

    def test_instance_to_rest(self):
        from pgi.repository import Gtk

        def itr(gprop):
            return instance_to_rest(gprop.value_type.pytype, gprop.default_value)

        v = instance_to_rest(Gtk.AccelFlags, Gtk.AccelFlags.LOCKED)
        self.assertEqual(v,
            ":obj:`Gtk.AccelFlags.LOCKED` | :obj:`Gtk.AccelFlags.MASK`")

        v = instance_to_rest(int, long_(42))
        self.assertEqual(v, "``42``")

        v = instance_to_rest(Gtk.Button, None)
        self.assertEqual(v, ":obj:`None`")

        v = itr(Gtk.Widget.props.no_show_all)
        self.assertEqual(v, ":obj:`False`")

        v = instance_to_rest(
            Gtk.ImageType, Gtk.ImageType(int(Gtk.ImageType.EMPTY)))
        self.assertEqual(v, ":obj:`Gtk.ImageType.EMPTY`")

        v = itr(Gtk.AboutDialog.props.program_name)
        self.assertEqual(v, ":obj:`None`")

        v = itr(Gtk.IMContext.props.input_hints)
        self.assertEqual(v, ":obj:`Gtk.InputHints.NONE`")

        v = itr(Gtk.CellRendererAccel.props.accel_mods)
        self.assertEqual(v, "``0``")

    def test_child_properties(self):
        from pgi.repository import Gtk

        self.assertEqual(len(get_child_properties(Gtk.Paned)), 2)
        self.assertFalse(get_child_properties(Gtk.Bin))
        self.assertEqual(len(get_child_properties(Gtk.ActionBar)), 2)
        self.assertEqual(len(get_child_properties(Gtk.Box)), 5)
        self.assertFalse(get_child_properties(Gtk.Statusbar))

    def test_style_properties(self):
        from pgi.repository import Gtk

        self.assertEqual(len(get_style_properties(Gtk.Paned)), 1)
        self.assertEqual(len(get_style_properties(Gtk.Widget)), 17)
        self.assertEqual(len(get_style_properties(Gtk.TreeView)), 11)

    def test_fake_subclasses(self):
        from pgi.repository import Gtk

        self.assertIs(fake_subclasses(Gtk.Scrollable)[1], Gtk.TreeView)

    def test_unescape(self):
        self.assertEqual(unescape_parameter("print_"), "print")
        self.assertEqual(unescape_parameter("exec_"), "exec")
        self.assertEqual(unescape_parameter("_print"), "-print")
        self.assertEqual(unescape_parameter("_3"), "3")

    def test_fake_bases(self):
        from pgi.repository import Atk, GObject

        self.assertEqual(
            fake_bases(Atk.ImplementorIface), [GObject.GInterface])

    def test_fake_bases_ignore_redundant(self):
        from pgi.repository import Gtk

        self.assertEqual(
            fake_bases(Gtk.Dialog, ignore_redundant=True), [Gtk.Window])
