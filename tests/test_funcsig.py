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

        sig = FuncSignature.from_string("do_get_item_attributes",
            "do_get_item_attributes(item_index: int) -> "
            "attributes: {str: GLib.Variant}")

        self.assertEqual(sig.res, [["attributes", "{str: GLib.Variant}"]])

    def test_to_simple_sig(self):
        sig = FuncSignature.from_string("to_hash",
            "to_hash(flags: NetworkManager.SettingHashFlags, foo: [int]) -> "
            "{str: {int: int}}")
        self.assertEqual(sig.to_simple_signature(), "(flags, foo)")

    def test_to_simple_sig_2(self):
        sig = FuncSignature.from_string("to_hash",
            "to_hash(flags: Foo.Bar, foo: [int or None], *data)")
        self.assertEqual(sig.to_simple_signature(), "(flags, foo, *data)")

    def test_arg_to_class_ref(self):
        self.assertEqual(arg_to_class_ref("bytes"), ":obj:`bytes <str>`")
        self.assertEqual(arg_to_class_ref("int"), ":obj:`int`")
        self.assertEqual(arg_to_class_ref("[int]"), "[:obj:`int`]")
        self.assertEqual(
            arg_to_class_ref("[Gtk.Window]"), "[:obj:`Gtk.Window`]")
        self.assertEqual(
            arg_to_class_ref("{Gtk.Window or None: int}"),
            "{:obj:`Gtk.Window` or :obj:`None`: :obj:`int`}")
        self.assertEqual(
            arg_to_class_ref("[str] or None"),
            "[:obj:`str`] or :obj:`None`")
        self.assertEqual(arg_to_class_ref(""), "")

    def test_to_rest_listing(self):

        class FakeRepo(object):

            def lookup_docs(self, type_, name, *args, **kwargs):
                if "para" in type_:
                    return escape_rest("PARADOC(%s)" % name), ""
                return escape_rest("RETURNDOC(%s)" % name), ""

        sig = FuncSignature.from_string("go", "go(*args)")
        doc = sig.to_rest_listing(FakeRepo(), "Foo.bar.go")
        # no empty reST references
        self.assertTrue("``" not in doc)

        sig = FuncSignature.from_string(
            "go", "go(a_: [str]) -> int, b_: [str]")
        doc = sig.to_rest_listing(FakeRepo(), "Foo.bar.go")
        self.assertEqual(doc, """\
:param a\\_:
    PARADOC(Foo.bar.go.a\\_)

:type a\\_: [:obj:`str`]
:returns:
    RETURNDOC(Foo.bar.go)
    
    :b\\_:
        PARADOC(Foo.bar.go.b\\_)

:rtype: (:obj:`int`, **b\\_**: [:obj:`str`])\
""")

        sig = FuncSignature.from_string("go", "go(*args: int)")
        doc = sig.to_rest_listing(FakeRepo(), "Foo.bar.go")
        self.assertEqual(doc, """\
:param args:
    PARADOC(Foo.bar.go.args)

:type args: :obj:`int`\
""")

        # only one out param
        sig = FuncSignature.from_string("go", "go() -> foo: int")
        doc = sig.to_rest_listing(FakeRepo(), "Foo.bar.go")
        self.assertEqual(doc, """\
:returns:
    PARADOC(Foo.bar.go.foo)

:rtype: **foo**: :obj:`int`\
""")
