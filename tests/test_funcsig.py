# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import unittest

from pgidocgen.funcsig import FuncSignature, arg_to_class_ref
from pgidocgen.util import escape_rest


class TFuncSigs(unittest.TestCase):

    def test_from_string(self):
        sig = FuncSignature.from_string("foo", "foo(bar: int)")
        self.assertTrue(sig)
        self.assertEqual(sig.name, "foo")
        self.assertEqual(sig.args, [["bar", "int"]])
        self.assertEqual(sig.res, [])
        self.assertEqual(sig.raises, False)

    def test_from_string_res(self):
        sig = FuncSignature.from_string("foo", "foo() -> int")
        self.assertEqual(sig.res, [["int"]])

    def test_from_string_2(self):
        sig = FuncSignature.from_string(
            "init", "init(argv: [str] or None) -> argv: [str]")
        self.assertTrue(sig)
        self.assertEqual(sig.name, "init")
        self.assertEqual(sig.args, [["argv", "[str] or None"]])
        self.assertEqual(sig.res, [["argv", "[str]"]])
        self.assertEqual(sig.raises, False)

    def test_from_string_args(self):
        sig = FuncSignature.from_string(
            "init", "init(foo: bool, *args: int)")
        self.assertTrue(sig)
        self.assertEqual(sig.name, "init")
        self.assertEqual(sig.raises, False)
        self.assertEqual(sig.args, [["foo", "bool"], ["*args", "int"]])

    def test_from_string_notype(self):
        sig = FuncSignature.from_string(
            "init", "init(foo)")
        self.assertEqual(sig.args, [["foo", ""]])

    def test_from_string_raises(self):
        sig = FuncSignature.from_string("init", "init(foo)")
        self.assertEqual(sig.raises, False)

        sig = FuncSignature.from_string("init", "init(foo) raises")
        self.assertEqual(sig.raises, True)

    def test_from_string_hash(self):
        sig = FuncSignature.from_string("to_hash",
            "to_hash(flags: NetworkManager.SettingHashFlags) -> "
            "{str: {int: int}}")

        self.assertEqual(sig.res, [["{str: {int: int}}"]])

    def test_arg_to_class_ref(self):
        self.assertEqual(arg_to_class_ref("int"), ":obj:`int`")
        self.assertEqual(arg_to_class_ref("[int]"), "[:obj:`int`]")
        self.assertEqual(
            arg_to_class_ref("[Gtk.Window]"), "[:class:`Gtk.Window`]")
        self.assertEqual(
            arg_to_class_ref("{Gtk.Window or None: int}"),
            "{:class:`Gtk.Window` or :obj:`None`: :obj:`int`}")
        self.assertEqual(
            arg_to_class_ref("[str] or None"),
            "[:obj:`str`] or :obj:`None`")

    def test_to_rest_listing(self):
        sig = FuncSignature.from_string("go", "go(a_: [str]) -> b_: [str]")

        class FakeRepo(object):

            def lookup_parameter_docs(self, name):
                return escape_rest("PARADOC(%s)" % name)

            def lookup_return_docs(self, name):
                return escape_rest("RETURNDOC(%s)" % name)

        doc = sig.to_rest_listing(FakeRepo(), "Foo.bar.go")
        self.assertEqual(doc, """\
:param a\\_:
    PARADOC(Foo.bar.go.a\\_)

:type a\\_: [:obj:`str`]
:returns:
    RETURNDOC(Foo.bar.go)

:rtype: b\\_: [:obj:`str`]\
""")

        sig = FuncSignature.from_string("go", "go(*args: int)")
        doc = sig.to_rest_listing(FakeRepo(), "Foo.bar.go")
        self.assertEqual(doc, """\
:param args:
    PARADOC(Foo.bar.go.args)

:type args: :obj:`int`
:returns:
    RETURNDOC(Foo.bar.go)
""")
