# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import re
import unittest

from pgidocgen.util import import_namespace
from pgidocgen.girdata import Library, Project, \
    get_docref_dir, get_docref_path, get_class_image_dir, \
    get_class_image_path, get_project_summary


class TGIRData(unittest.TestCase):

    def test_get_project_summary(self):
        s = get_project_summary("Gtk", "3.0")
        assert s.name == "gtk (Multi-platform toolkit)"
        assert s.description.startswith("GTK is a")
        assert s.homepage
        assert s.bugtracker
        assert s.mailinglists
        assert s.repositories

        get_project_summary("GIRepository", "1.0")
        get_project_summary("GstVideo", "1.0")

    def test_get_library_version(self):
        mods = ["Gtk-3.0", "Atk-1.0", "Gst-1.0", "Poppler-0.18", "Anthy-9000",
                "InputPad-1.0", "Pango-1.0", "WebKit2-4.0", "GdkPixbuf-2.0",
                "LunarDate-2.0", "TotemPlParser-1.0", "GVnc-1.0"]

        for m in mods:
            ns, version = m.split("-", 1)
            try:
                import_namespace(ns, version)
            except ImportError:
                continue
            lib = Library.for_namespace(ns, version)
            assert lib.version

    def test_get_project_version(self):
        self.assertEqual(
            Project.for_namespace("GObject").version,
            Project.for_namespace("GLib").version)

    def test_get_tag(self):

        def get_tag(namespace):
            return Project.for_namespace(namespace).get_tag()

        self.assertTrue(re.match(r"\d+\.\d+\.\d+", get_tag("Gtk")))
        self.assertTrue(re.match(r"ATK_\d+_\d+_\d+", get_tag("Atk")))
        self.assertTrue(re.match(r"\d+\.\d+\.\d+", get_tag("Gst")))
        self.assertFalse(get_tag("Nope"))

    def test_get_docref_dir(self):
        self.assertTrue(os.path.isdir(get_docref_dir()))

    def test_get_docref_path(self):
        self.assertTrue(os.path.isfile(get_docref_path("Gtk", "3.0")))

    def test_get_class_image_dir(self):
        self.assertTrue(os.path.isdir(get_class_image_dir("Gtk", "3.0")))

    def test_get_class_image_path(self):
        self.assertTrue(
            os.path.isfile(get_class_image_path("Gtk", "3.0", "Window")))

    def test_get_source_func(self):

        def get_url(namespace, path):
            project = Project.for_namespace(namespace)
            func = project.get_source_func(namespace)
            if not func:
                return ""
            return func(path)

        import_namespace("GstApp", "1.0")
        import_namespace("GstAllocators", "1.0")
        import_namespace("GstAudio", "1.0")
        import_namespace("GstPbutils", "1.0")

        url = get_url("Gtk", "gtk/gtktoolshell.c:30")
        self.assertTrue(
            re.match(r"https://gitlab\.gnome\.org/GNOME/gtk/blob/"
                     r"\d+\.\d+\.\d+/gtk/gtktoolshell\.c#L30", url))

        url = get_url("Gst", "gst/gstelementfactory.c:430")
        # https://gitlab.freedesktop.org/gstreamer/gstreamer/blob/1.14.4/gst/gstelementfactory.c#L430
        self.assertTrue(
            re.match(r"https://gitlab\.freedesktop\.org/gstreamer/"
                     r"gstreamer/blob/\d+\.\d+\.\d+/"
                     r"gst/gstelementfactory\.c\#L\d+", url))

        url = get_url("GstApp", "gst-libs/gst/app/gstappsrc.c:1237")
        self.assertTrue(
            re.match(r"https://gitlab\.freedesktop\.org/gstreamer/"
                     r"gst-plugins-base/blob/\d+\.\d+\.\d+/"
                     r"gst-libs/gst/app/gstappsrc\.c\#L\d+", url))

        url = get_url("GstRtsp", "gst-libs/gst/rtsp/gstrtspurl.c:97")
        self.assertTrue(
            re.match(r"https://gitlab\.freedesktop\.org/gstreamer/"
                     r"gst-plugins-base/blob/\d+\.\d+\.\d+/"
                     r"gst-libs/gst/rtsp/gstrtspurl\.c\#L\d+", url))
