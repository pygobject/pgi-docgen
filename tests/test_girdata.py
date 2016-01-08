# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import unittest

from pgidocgen.util import import_namespace
from pgidocgen.girdata import get_library_version, get_project_version, \
    get_tag, get_docref_dir, get_docref_path, get_class_image_dir, \
    get_class_image_path, get_source_to_url_func


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
            get_project_version(import_namespace("GObject", "2.0")),
            get_library_version(import_namespace("GLib", "2.0")))

    def test_get_tag(self):
        self.assertEqual(get_tag("Gtk", "3.18.8"), "3.18.8")
        self.assertEqual(get_tag("Atk", "1.14.8"), "ATK_1_14_8")
        self.assertEqual(get_tag("Gst", "1.6.2.0"), "1.6.2")
        self.assertEqual(get_tag("Nope", "1.6.2.0"), "")

    def test_get_docref_dir(self):
        self.assertTrue(os.path.isdir(get_docref_dir()))

    def test_get_docref_path(self):
        self.assertTrue(os.path.isfile(get_docref_path("Gtk", "3.0")))

    def test_get_class_image_dir(self):
        self.assertTrue(os.path.isdir(get_class_image_dir("Gtk", "3.0")))

    def test_get_class_image_path(self):
        self.assertTrue(
            os.path.isfile(get_class_image_path("Gtk", "3.0", "Window")))

    def test_get_source_to_url_func(self):
        func = get_source_to_url_func("Gtk", "3.18.0")
        self.assertEqual(
            func("gtk/gtktoolshell.c:30"),
            ("https://git.gnome.org/browse/gtk+/tree/gtk/gtktoolshell.c"
             "?h=3.18.0#n30"))

        func = get_source_to_url_func("Gst", "1.6.2.0")
        self.assertEqual(
            func("gst/gstelementfactory.c:430"),
            ("http://cgit.freedesktop.org/gstreamer/gstreamer/tree/gst/"
             "gstelementfactory.c?h=1.6.2#n430"))

        func = get_source_to_url_func("GstApp", "1.6.2.0")
        self.assertEqual(
            func("app/gstappsrc.c:1237"),
            ("http://cgit.freedesktop.org/gstreamer/gst-plugins-base/tree/"
             "gst-libs/gst/app/gstappsrc.c?h=1.6.2#n1237"))

        func = get_source_to_url_func("GstRtsp", "1.6.2.0")
        self.assertEqual(
            func("rtsp/gstrtspurl.c:97"),
            ("http://cgit.freedesktop.org/gstreamer/gst-plugins-base/tree/"
             "gst-libs/gst/rtsp/gstrtspurl.c?h=1.6.2#n97"))
