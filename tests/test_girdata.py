# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import unittest

from pgidocgen.util import import_namespace
from pgidocgen.girdata import get_library_version, get_project_version


class TGIRData(unittest.TestCase):

    def test_get_library_version(self):
        mods = ["Gtk", "Atk", "Gst", "Poppler", "Anthy", "InputPad", "Pango",
                "WebKit2", "GdkPixbuf", "LunarDate", "TotemPlParser", "GVnc"]

        for m in mods:
            try:
                m = import_namespace(m)
            except ImportError:
                continue
            self.assertTrue(get_library_version(m))

    def test_get_project_version(self):
        self.assertEqual(
            get_project_version(import_namespace("GObject")),
            get_library_version(import_namespace("GLib")))
