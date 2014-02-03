# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import unittest

from pgidocgen.module import get_project_summary


class TDoap(unittest.TestCase):

    def test_doap(self):
        self.assertFalse(get_project_summary("Nope", "99.0"))
        self.assertTrue(get_project_summary("Gtk", "3.0"))
        self.assertTrue(get_project_summary("Gst", "1.0"))
        self.assertTrue(get_project_summary("Atk", "1.0"))
        self.assertTrue(get_project_summary("GLib", "2.0"))
        self.assertTrue(get_project_summary("Cogl", "1.0"))
