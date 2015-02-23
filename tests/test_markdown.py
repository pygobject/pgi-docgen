# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


import unittest

from pgidocgen.markdown import markdown2docbook
from pgidocgen.repo import docstring_to_rest


class TMarkdown(unittest.TestCase):

    def test_basic(self):
        md_example = u"""\
identifier:

documentation ...

# Height-for-width Geometry Management # {#geometry-management}

# A level-one header with a [link](/url) and *emphasis*

## adsad ##

### afaf ###

Here is some `inline code`

Documentation:

- list item 1
- list item 2 [link](/url) foo

Even more docs.\
"""

        expected = """\
<para>identifier:</para>
<para>documentation ...</para>
<title>Height-for-width Geometry Management</title>
<title>A level-one header with a <ulink url="/url">link</ulink> and <emphasis>emphasis</emphasis></title>
<subtitle>adsad</subtitle>
<subtitle>afaf</subtitle>
<para>Here is some <literal>inline code</literal></para>
<para>Documentation:</para>
<itemizedlist>
<listitem>list item 1</listitem>
<listitem>list item 2 <ulink url="/url">link</ulink> foo</listitem>
</itemizedlist>
<para>Even more docs.</para>\
"""

        rst_expected = """\
identifier\:
documentation ...
Height-for-width Geometry Management
A level-one header with alinkandemphasis
adsad
afaf
Here is some ``inline code``
Documentation\:


* list item 1
* list item 2 `link </url>`__ foo


Even more docs.\
"""

        docbook = markdown2docbook(md_example)
        self.assertEqual(docbook, expected, msg=docbook)
        rest = docstring_to_rest({}, "Foo.Bar", docbook)
        self.assertEqual(rest, rst_expected, msg=rest)
