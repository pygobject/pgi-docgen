# Copyright 2013, 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import unittest

from pgidocgen.girdata import get_project_summary, get_doap_dir


class TDoap(unittest.TestCase):

    def test_doap(self):
        self.assertFalse(get_project_summary("Nope"))

        for entry in os.listdir(get_doap_dir()):
            name = os.path.splitext(entry)[0]
            self.assertTrue(get_project_summary(name), msg=name)
