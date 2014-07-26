# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import unittest

from pgidocgen.util import is_staticmethod, is_classmethod, is_normalmethod
from pgidocgen.util import is_method_owner, is_fundamental, is_object
from pgidocgen.util import instance_to_rest, get_child_properties
from pgidocgen.util import fake_subclasses


class TUtil(unittest.TestCase):

    def test_method_checks(self):

        class SomeClass(object):

            @classmethod
            def x(cls):
                pass

            @staticmethod
            def y():
                pass

            def z(self):
                pass

        self.assertTrue(is_classmethod(SomeClass.x))
        self.assertFalse(is_staticmethod(SomeClass.x))
        self.assertFalse(is_normalmethod(SomeClass.x))

        self.assertTrue(is_staticmethod(SomeClass.y))
        self.assertFalse(is_classmethod(SomeClass.y))
        self.assertFalse(is_normalmethod(SomeClass.y))

        self.assertFalse(is_classmethod(SomeClass.z))
        self.assertFalse(is_staticmethod(SomeClass.z))
        self.assertTrue(is_normalmethod(SomeClass.z))

    def test_is_method_owner(self):
        from pgi.repository import Gtk

        self.assertTrue(is_method_owner(Gtk.ActionGroup, "add_actions"))
        self.assertFalse(is_method_owner(Gtk.Range, "get_has_tooltip"))
        if os.name != "nt":
            self.assertTrue(is_method_owner(Gtk.Plug, "new"))
        self.assertTrue(is_method_owner(Gtk.Viewport, "get_vadjustment"))
        self.assertTrue(is_method_owner(Gtk.AccelGroup, "connect"))
        self.assertFalse(is_method_owner(Gtk.AboutDialog, "get_focus_on_map"))

    def test_class_checks(self):
        from pgi.repository import GObject

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

        v = instance_to_rest(int, 42L)
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

    def test_fake_subclasses(self):
        from pgi.repository import Gtk

        self.assertIs(fake_subclasses(Gtk.Scrollable)[1], Gtk.TreeView)
