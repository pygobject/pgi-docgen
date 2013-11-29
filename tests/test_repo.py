# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import unittest

from pgidocgen.repo import FuncSignature, arg_to_class_ref


class TFuncSigs(unittest.TestCase):

    def test_from_string(self):
        sig = FuncSignature.from_string("foo", "foo(bar: int)")
        self.assertTrue(sig)
        self.assertEqual(sig.name, "foo")
        self.assertEqual(sig.args, [["bar", "int"]])
        self.assertEqual(sig.res, [])
        self.assertEqual(sig.raises, False)

    def test_from_string_2(self):
        sig = FuncSignature.from_string(
            "init", "init(argv: [str] or None) -> argv: [str]")
        self.assertTrue(sig)
        self.assertEqual(sig.name, "init")
        self.assertEqual(sig.args, [["argv", "[str] or None"]])
        self.assertEqual(sig.res, [["argv", "[str]"]])
        self.assertEqual(sig.raises, False)

    def test_arg_to_class_ref(self):
        self.assertEqual(arg_to_class_ref("int"), ":class:`int`")
        self.assertEqual(arg_to_class_ref("[int]"), "[:class:`int`]")
        self.assertEqual(
            arg_to_class_ref("[Gtk.Window]"), "[:class:`Gtk.Window`]")
        self.assertEqual(
            arg_to_class_ref("{Gtk.Window or None: int}"),
            "{:class:`Gtk.Window` or :obj:`None`: :class:`int`}")
        self.assertEqual(
            arg_to_class_ref("[str] or None"),
            "[:class:`str`] or :obj:`None`")
