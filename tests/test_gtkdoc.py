# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import unittest

from pgidocgen.gtkdoc import ConvertMarkDown


class TGTKDoc(unittest.TestCase):

    def test_main(self):
        input_ = """\
SUPPORTED MARKDOWN
==================

Atx-style Headers
-----------------

# Header 1

## Header 2 ##

Setext-style Headers
--------------------

Header 1
========

Header 2
--------

Ordered (unnested) Lists
------------------------

1. item 1

1. item 2 with loooong *foo*
   description

3. item 3

Note: we require a blank line above the list items
"""

        expexted = """\
<para>SUPPORTED MARKDOWN</para>
<para>Atx-style Headers</para>
<refsect2><title>Header 1</title><refsect3><title>Header 2</title></refsect3>
<refsect3><title>Setext-style Headers</title></refsect3>
</refsect2>
<refsect2><title>Header 1</title><para>Header 2</para>
<para>Ordered (unnested) Lists</para>
<orderedlist>
<listitem>
<para>item 1</para>
</listitem>
<listitem>
<para>item 2 with loooong *foo*
description</para>
</listitem>
<listitem>
<para>item 3</para>
</listitem>
</orderedlist>
<para>Note: we require a blank line above the list items</para>
</refsect2>
"""

        output = ConvertMarkDown("", input_)
        self.assertEqual(expexted, output)

    def test_docbook(self):
        input_ = """\
<itemizedlist>
  <listitem>#GtkWidgetClass.get_request_mode()</listitem>
  <listitem>#GtkWidgetClass.get_preferred_width()</listitem>
  <listitem>#GtkWidgetClass.get_preferred_height()</listitem>
  <listitem>#GtkWidgetClass.get_preferred_height_for_width()</listitem>
  <listitem>#GtkWidgetClass.get_preferred_width_for_height()</listitem>
  <listitem>#GtkWidgetClass.get_preferred_height_and_baseline_for_width()</listitem>
</itemizedlist>
"""

        # docbook should stay the same
        output = ConvertMarkDown("", input_)
        self.assertEqual(input_, output)
