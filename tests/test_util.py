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
