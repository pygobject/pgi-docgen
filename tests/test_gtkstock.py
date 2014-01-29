# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import unittest

from pgidocgen.gtkstock import parse_stock_icon


class TGtkStock(unittest.TestCase):

    @unittest.skipIf(os.name == "nt", "windows..")
    def test_parse_stock_icon(self):
        url = ("../../stockicons/")
        doc = parse_stock_icon("Gtk.STOCK_ORIENTATION_LANDSCAPE")
        self.assertTrue(".. image:: " + url in doc)
        self.assertTrue(":alt: gtk-orientation-landscape.png" in doc)
