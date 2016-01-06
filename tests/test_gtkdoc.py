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

    def test_header(self):
        input_ = """
widget lifecycle, states and style.

# Height-for-width Geometry Management # {#geometry-management}

GTK+ uses a height-for-width (and wid
"""

        expected = """\
<para>widget lifecycle, states and style.</para>
<refsect2 id="geometry-management"><title>Height-for-width Geometry Management</title><para>GTK+ uses a height-for-width (and wid</para>
</refsect2>
"""

        output = ConvertMarkDown("", input_)
        self.assertEqual(expected, output)

    def test_lists(self):
        input_ = """\
bla bla
bla:

- The channel was just created, and has not been written to or read from yet.
  bla

- The channel is write-only.

foo
"""
        expected = """\
<para>bla bla
bla:</para>
<itemizedlist>
<listitem>
<para>The channel was just created, and has not been written to or read from yet.
bla</para>
</listitem>
<listitem>
<para>The channel is write-only.</para>
</listitem>
</itemizedlist>
<para>foo</para>
"""
        output = ConvertMarkDown("", input_)
        self.assertEqual(expected, output)

    def test_paragraphs(self):
        input_ = """\
foo,
bar.

foo,
bar.

foo,
bar.
"""
        expected = """\
<para>foo,
bar.</para>
<para>foo,
bar.</para>
<para>foo,
bar.</para>
"""
        output = ConvertMarkDown("", input_)
        self.assertEqual(expected, output)

    def test_reference(self):
        input_ = """\
The #GData struct is an opaque data structure to represent a
[Keyed Data List][glib-Keyed-Data-Lists]. It should only be
accessed via the following functions."""

        expected = """\
<para>The #GData struct is an opaque data structure to represent a
<link linkend="glib-Keyed-Data-Lists">Keyed Data List</link>. It should only be
accessed via the following functions.</para>
"""

        output = ConvertMarkDown("", input_)
        self.assertEqual(expected, output)

    def test_reference2(self):
        input_ = "a [foo][bar] b [quux][baz]"
        expected = '<para>a <link linkend="bar">foo</link> b <link linkend="baz">quux</link></para>\n'
        output = ConvertMarkDown("", input_)
        self.assertEqual(expected, output)

    def test_reference_empty(self):
        input_ = "[][]"
        expected = '<para><ulink url=""></ulink></para>\n'
        output = ConvertMarkDown("", input_)
        self.assertEqual(expected, output)

    def test_inline_code(self):
        input_ = "a `abc`"
        expected = '<para>a <literal>abc</literal></para>\n'
        output = ConvertMarkDown("", input_)
        self.assertEqual(expected, output)

    def test_inline_code2(self):
        input_ = "a `[][]`"
        expected = '<para>a <literal>[][]</literal></para>\n'
        output = ConvertMarkDown("", input_)
        self.assertEqual(expected, output)

    def test_code(self):
        input_ = """\
|[<!-- language="C" -->
    GdkEvent *event;
    GdkEventType type;

    type = event->type;
]|
"""

        expected = '''\
<informalexample><programlisting language="C"><![CDATA[
    GdkEvent *event;
    GdkEventType type;

    type = event->type;
]]></programlisting></informalexample>
<para></para>
'''
        output = ConvertMarkDown("", input_)
        self.assertEqual(expected, output)
