# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


import unittest

from pgidocgen.markdown import markdown2rest


class TMarkdown(unittest.TestCase):

    def test_basic(self):
        md_example = u"""\
identifier:

documentation ...

# Height-for-width Geometry Management # {#geometry-management}

# A level-one header with a [link](/url) and *emphasis*

## adsad ##

### afaf ###

Documentation:

- list item 1
- list item 2 [link](/url)

Even more docs.\
"""

        expected = """\
identifier:

documentation ...

Height-for-width Geometry Management
====================================

A level-one header with a  `link </url>`__  and  *emphasis*
===========================================================

adsad
-----

afaf
^^^^

Documentation:

* list item 1
* list item 2  `link </url>`__

Even more docs.\
"""

        self.assertEqual(markdown2rest(md_example), expected)
