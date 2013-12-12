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
