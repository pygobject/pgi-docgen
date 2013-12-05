# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import unittest

from pgidocgen.util import is_staticmethod, is_classmethod, is_normalmethod


class TUtil(unittest.TestCase):

    def test_method_checks(self):

        class SomeClass(object):

            @classmethod
            def x(cls):
                pass

            @staticmethod
            def y():
                pass

            def z(self):
                pass

        self.assertTrue(is_classmethod(SomeClass.x))
        self.assertFalse(is_staticmethod(SomeClass.x))
        self.assertFalse(is_normalmethod(SomeClass.x))

        self.assertTrue(is_staticmethod(SomeClass.y))
        self.assertFalse(is_classmethod(SomeClass.y))
        self.assertFalse(is_normalmethod(SomeClass.y))

        self.assertFalse(is_classmethod(SomeClass.z))
        self.assertFalse(is_staticmethod(SomeClass.z))
        self.assertTrue(is_normalmethod(SomeClass.z))

