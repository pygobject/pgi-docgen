# Copyright 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import unittest

from pgidocgen.docbook_escape import docbook_escape


class Tdocbook_escape(unittest.TestCase):

    def test_main(self):
        self.assertEqual(docbook_escape(""), "")
        self.assertEqual(docbook_escape("foo"), "foo")

    def test_escape(self):
        self.assertEqual(
            docbook_escape("<bla></bla>"), "&lt;bla&gt;&lt;/bla&gt;")
        self.assertEqual(docbook_escape("<sect4></sect4>"), "<sect4></sect4>")

    def test_real_example(self):
        self.assertEqual(
            docbook_escape("""\
The GtkFileFilter implementation of the GtkBuildable interface
supports adding rules using the <mime-types>, <patterns> and
<applications> elements and listing the rules within. Specifying
a <mime-type> or <pattern> has the same effect as as calling
gtk_file_filter_add_mime_type() or gtk_file_filter_add_pattern().
"""), """\
The GtkFileFilter implementation of the GtkBuildable interface
supports adding rules using the &lt;mime-types&gt;, &lt;patterns&gt; and
&lt;applications&gt; elements and listing the rules within. Specifying
a &lt;mime-type&gt; or &lt;pattern&gt; has the same effect as as calling
gtk_file_filter_add_mime_type() or gtk_file_filter_add_pattern().
""")
