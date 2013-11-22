#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from gen.repo import FuncSignature, arg_to_class_ref


if __name__ == '__main__':

    sig = FuncSignature.from_string("foo", "foo(bar: int)")
    assert sig
    assert sig.name == "foo"
    assert sig.args == [["bar", "int"]]
    assert sig.res == []
    assert sig.raises == False

    sig = FuncSignature.from_string(
        "init", "init(argv: [str] or None) -> argv: [str]")
    assert sig
    assert sig.name == "init"
    assert sig.args == [["argv", "[str] or None"]]
    assert sig.res == [["argv", "[str]"]]
    assert sig.raises == False

    assert arg_to_class_ref("int") == ":class:`int`"
    assert arg_to_class_ref("[int]") == "[:class:`int`]"
    assert arg_to_class_ref("[Gtk.Window]") == "[:class:`Gtk.Window`]"
    assert arg_to_class_ref("{Gtk.Window or None: int}") == \
        "{:class:`Gtk.Window` or :obj:`None`: :class:`int`}"
    assert arg_to_class_ref("[str] or None") == \
        "[:class:`str`] or :obj:`None`"
