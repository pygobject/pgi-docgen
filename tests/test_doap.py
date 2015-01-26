# Copyright 2013, 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import unittest

from pgidocgen.doap import get_project_summary


class TDoap(unittest.TestCase):

    def test_doap(self):
        self.assertFalse(get_project_summary(".", "Nope", "99.0"))

        for entry in os.listdir(os.path.join("data", "doap")):
            name, version = entry.rsplit(".", 1)[0].split("-")
            self.assertTrue(get_project_summary(".", name, version), msg=name)
