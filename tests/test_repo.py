# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


import unittest

from pgidocgen.repo import Repository


class TRepository(unittest.TestCase):

    def test_pango(self):
        repo = Repository("Pango", "1.0")

        self.assertTrue(
            repo.lookup_parameter_docs("Pango.extents_to_pixels.inclusive"))

        self.assertTrue(
            repo.lookup_parameter_docs("Pango.break_.text"))

        self.assertTrue(repo.is_private("Pango.RendererPrivate"))
        self.assertFalse(repo.is_private("Pango.AttrIterator"))

    def test_gio(self):
        repo = Repository("Gio", "2.0")

        method = repo.lookup_attr_docs("Gio.Application.activate")
        signal = repo.lookup_signal_docs("Gio.Application.activate")

        self.assertTrue(method)
        self.assertTrue(signal)
        self.assertNotEqual(method, signal)

    def test_properties(self):
        repo = Repository("Gio", "2.0")
        print repo.lookup_prop_docs("Gio.Application.action-group")

    def test_other(self):
        Repository("GLib", "2.0")
        Repository("GObject", "2.0")

    def test_version_added(self):
        repo = Repository("Atk", "1.0")
        docs = repo.lookup_attr_meta("Atk.Document.get_attributes")
        self.assertTrue(".. versionadded:: 1.12" in docs)

        docs = repo.lookup_attr_meta("Atk.Document.get_attribute_value")
        self.assertTrue(".. versionadded:: 1.12" in docs)

    def test_deprecated(self):
        repo = Repository("Atk", "1.0")
        docs = repo.lookup_attr_meta("Atk.Hyperlink.is_selected_link")
        self.assertTrue(".. deprecated::" in docs)
