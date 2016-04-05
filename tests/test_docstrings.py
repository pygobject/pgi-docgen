# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import unittest

from pgidocgen.repo import docstring_to_rest
from pgidocgen.namespace import get_base_types


class DummyRepo(object):

    def __init__(self):
        self.types = {
            "g_rand_new_with_seed": ["GLib.Rand.new_with_seed"],
            "GQuark": ["GLib.Quark"],
            "GTypeInterface": ["GObject.TypeInterface"],
            "g_value_copy": ["GObject.Value.copy"],
            "GtkCellEditable": ["Gtk.CellEditable"],
            "gtk_tree_model_get": ["Gtk.TreeModel.get"],
            "GTK_TREE_VIEW_COLUMN_AUTOSIZE": ["Gtk.TreeViewColumnSizing.AUTOSIZE"],
            "AtkTextAttribute": ["Atk.TextAttribute"],
            "ATK_TEXT_ATTR_INVALID": ["Atk.TextAttribute.INVALID"],
            "GtkApplication": ["Gtk.Application"],
            "GtkCellEditable": ["Gtk.CellEditable"],
            "ATK_RELATION_NULL": ["Atk.RelationType.NULL"],
            "AtkObject": ["Atk.Object"],
            "AtkTable": ["Atk.Table"],
            "GtkSettings": ["Gtk.Settings"],
            "GtkContainer": ["Gtk.Container"],
            "GdkFrameTimings": ["Gdk.FrameTimings"],
            "GtkWidget": ["Gtk.Widget"],
            "GtkRecentFilterInfo": ["Gtk.RecentFilterInfo"],
        }
        self.types.update(get_base_types())

        self.docrefs = {
            "im-a-ref": "http://example.com",
        }

        self.type_structs = {
            "GtkWidgetClass": "Gtk.Widget",
        }

        self.instance_params = {
            "Gtk.TreeModel.get": "tree_model"
        }

    def lookup_gtkdoc_ref(self, doc_ref):
        return self.docrefs.get(doc_ref)

    def lookup_py_id(self, c_id):
        return self.types.get(c_id, [None])[0]

    def lookup_py_id_for_type_struct(self, c_id):
        return self.type_structs.get(c_id)

    def lookup_instance_param(self, py_id):
        return self.instance_params.get(py_id)


class TDocstring(unittest.TestCase):

    def setUp(self):
        self._repo = DummyRepo()

    def _check(self, text, expected, current_type=None, current_func=None):
        out = docstring_to_rest(self._repo, text, current_type, current_func)
        self.assertEqual(out, expected)

    def check(self, *args, **kwargs):
        return self._check(*args, **kwargs)

    def test_field(self):
        self.check(
            "#GtkRecentFilterInfo.contains",
            ":ref:`Gtk.RecentFilterInfo.contains <Gtk.RecentFilterInfo.fields>`")

    def test_booleans(self):
        self.check(
            "%TRUE foo bar, %FALSE bar.",
            ":obj:`True` foo bar, :obj:`False` bar.")

        self.check(
            "always returns %FALSE.",
            "always returns :obj:`False`.")

    def test_type(self):
        self.check(
            "a #GQuark id to identify the data",
            "a :obj:`GLib.Quark` id to identify the data")

        self.check(
            "implementing a #GtkContainer: a",
            "implementing a :obj:`Gtk.Container`\\: a")

    def test_method(self):
        self.check(
            "g_rand_new_with_seed()",
            ":obj:`GLib.Rand.new_with_seed`\\()")

    def test_type_unmarked(self):
        self.check(
            "The GTypeInterface structure",
            "The :obj:`GObject.TypeInterface` structure")

        self.check(
            "GQuark",
            ":obj:`GLib.Quark`")

    def test_params(self):
        self.check(
            "%TRUE if g_value_copy() with @src_type and @dest_type.",
            ":obj:`True` if :obj:`GObject.Value.copy`\\() with `src_type` and `dest_type`.")

        self.check(
            "@icon_set.",
            "`icon_set`.")

        self.check(
            "if @page is complete.",
            "if `page` is complete.")

        self.check(
            "in *@dest_x and ",
            "in `dest_x` and ")

        self.check("and a @foo\nbla", "and a `foo`\nbla")
        self.check("@one@two", "`one` `two`")

        self.check("at (@x, @y) bla", "at (`x`, `y`) bla")

    def test_instance_params(self):
        self.check(
            "a @tree_model and a @foo",
            "a `self` and a `foo`",
            "Gtk.TreeModel",
            "Gtk.TreeModel.get")

    def test_inline_code(self):
        self.check(
            "To free this list, you can use |[ g_slist_free_full (list, (GDestroyNotify) g_object_unref); ]|",
            "To free this list, you can use ``g_slist_free_full (list, (GDestroyNotify) g_object_unref);``")

        self.check(
            "a |[ blaa()\n ]| adsad",
            "a ``blaa()`` adsad")

    def test_escaped_xml(self):
        self.check(
            "target attribute on &lt;a&gt; elements.",
            "target attribute on <a> elements.")

        self.check(
            "This is called for each unknown element under &lt;child&gt;.",
            "This is called for each unknown element under <child>.")

    def test_docbook_programlisting(self):
        self.check("""
<informalexample><programlisting>
gtk_entry_buffer_get_length (gtk_entry_get_buffer (entry));
</programlisting></informalexample>""",
        "``gtk_entry_buffer_get_length (gtk_entry_get_buffer (entry));``")

        self.check(
            """\
foo
<programlisting>
foo;
bar;
</programlisting>
bar\
""",
            """\
foo


.. code-block:: none

    foo;
    bar;

bar\
""")

    def test_docbook_literal(self):
        self.check(
            "the unique ID for @window, or <literal>0</literal> if the",
            "the unique ID for `window`, or ``0`` if the")

        self.check(
            "you would\nwrite: <literal>;gtk_tree_model_get (model, iter, 0, &amp;place_string_here, -1)</literal>,\nwhere",
            "you would\nwrite\\: ``;gtk_tree_model_get (model, iter, 0, &place_string_here, -1)``,\nwhere")

        self.check(
            "where <literal>place_string_here</literal> is a",
            "where ``place_string_here`` is a")

        self.check(
            "a style class named <literal>level-</literal>@name",
            "a style class named ``level-`` `name`")

    def test_signal(self):
        self.check(
            "Emits the #GtkCellEditable::editing-done signal.",
            "Emits the :obj:`Gtk.CellEditable` :py:func:`::editing-done<Gtk.CellEditable.signals.editing_done>` signal.")

        self.check(
            "GtkWidget::foo_bar vfunc",
            "GtkWidget\\:\\:foo\\_bar vfunc")

        self.check(
            "GtkWidgetClass::foo",
            "GtkWidgetClass\\:\\:foo")

    def test_signal_no_type(self):
        self.check(
            "Returns the value of the ::columns signal.",
            "Returns the value of the :py:func:`::columns<Gtk.Widget.signals.columns>` signal.",
            "Gtk.Widget")

        self.check(
            "this is some ::signal-foo blah",
            "this is some :py:func:`::signal-foo<Gtk.Widget.signals.signal_foo>` blah",
            "Gtk.Widget")

    def test_null(self):
        self.check(
            "a filename or %NULL",
            "a filename or :obj:`None`")

        self.check(
            "the NULL state or initial state",
            "the :obj:`None` state or initial state")

        self.check(
            "%NULL-terminated",
            ":obj:`None`-terminated")

    def test_docbook_type(self):
        self.check(
            "is a <type>gchar*</type>\nto be filled",
            "is a ``gchar*``\nto be filled")

    def test_constant(self):
        self.check(
            "Please note\nthat @GTK_TREE_VIEW_COLUMN_AUTOSIZE are inefficient",
            "Please note\nthat :obj:`Gtk.TreeViewColumnSizing.AUTOSIZE` are inefficient")

    def test_list(self):
        self.check(
            """\
bla bla
bla:

- The channel was just created, and has not been written to or read from yet.
  bla

- The channel is write-only.

foo
""",
            """bla bla
bla\:


* The channel was just created, and has not been written to or read from yet.
  bla
* The channel is write-only.

foo
""")

    def test_docbook_itemizedlist(self):
        self.check(
            """\
<itemizedlist>
  <listitem>#GtkWidgetClass.get_request_mode()</listitem>
  <listitem>#GtkWidgetClass.get_preferred_width()</listitem>
  <listitem>#GtkWidgetClass.get_preferred_height()</listitem>
  <listitem>#GtkWidgetClass.get_preferred_height_for_width()</listitem>
  <listitem>#GtkWidgetClass.get_preferred_width_for_height()</listitem>
  <listitem>#GtkWidgetClass.get_preferred_height_and_baseline_for_width()</listitem>
</itemizedlist>
""",
            """
* :obj:`Gtk.Widget.do_get_request_mode`\\()
* :obj:`Gtk.Widget.do_get_preferred_width`\\()
* :obj:`Gtk.Widget.do_get_preferred_height`\\()
* :obj:`Gtk.Widget.do_get_preferred_height_for_width`\\()
* :obj:`Gtk.Widget.do_get_preferred_width_for_height`\\()
* :obj:`Gtk.Widget.do_get_preferred_height_and_baseline_for_width`\\()
""")

    def test_header(self):
        self.check(
            """\
GtkWidget is the base class all widgets in GTK+ derive from. It manages the
widget lifecycle, states and style.

# Height-for-width Geometry Management # {#geometry-management}

GTK+ uses a height-for-width (and width-for-height) geometry management
system. Height-for-width means that a widget can change how much
vertical space it needs, depending on the amount of horizontal space
that it is given (and similar for width-for-height). The most common
example is a label that reflows to fill up the available width, wraps
to fewer lines, and therefore needs less height.
""",
            """\
:obj:`Gtk.Widget` is the base class all widgets in GTK+ derive from. It manages the
widget lifecycle, states and style.


Height-for-width Geometry Management
    ..
        .

GTK+ uses a height-for-width (and width-for-height) geometry management
system. Height-for-width means that a widget can change how much
vertical space it needs, depending on the amount of horizontal space
that it is given (and similar for width-for-height). The most common
example is a label that reflows to fill up the available width, wraps
to fewer lines, and therefore needs less height.
""")

    def test_paragraphs(self):
        self.check(
            "foo,\nbar.\n\nfoo,\nbar.\n\nfoo,\nbar.\n",
            "foo,\nbar.\n\nfoo,\nbar.\n\nfoo,\nbar.\n")

    def test_unknown(self):
        self.check(
            " or #ATK_TEXT_ATTRIBUTE_INVALID if no match",
            "or #ATK\\_TEXT\\_ATTRIBUTE\\_INVALID if no match")

    def test_enum(self):
        self.check(
            "or #ATK_RELATION_NULL if",
            "or :obj:`Atk.RelationType.NULL` if")

    def test_escape_rest(self):
        self.check(
            "table by initializing **selected",
            "table by initializing \\*\\*selected")

        self.check(
            "Since: this is",
            "Since\\: this is")

        self.check(
            "unless it has handled or blocked `SIGPIPE'.",
            "unless it has handled or blocked \\`SIGPIPE'.")

    def test_type_plural(self):
        self.check(
            "captions are #AtkObjects",
            "captions are :obj:`Atk.Objects <Atk.Object>`")

        self.check(
            "foo #GdkFrameTiming",
            "foo :obj:`Gdk.FrameTiming <Gdk.FrameTimings>`")

    def test_property(self):
        self.check(
            "the #GtkSettings:gtk-error-bell setting",
            "the :obj:`Gtk.Settings` :py:data:`:gtk-error-bell<Gtk.Settings.props.gtk_error_bell>` setting")

    def test_base_types(self):
        self.check(
            "returns a gint*.",
            "returns a :obj:`int`.")

        self.check(
            "a #gint** that",
            "a :obj:`int` that")

        self.check(
            "returns a #gpointer",
            "returns a :obj:`object`")

    def test_docbook_keycombo(self):
        self.check(
            "<keycombo><keycap>Control</keycap><keycap>L</keycap></keycombo>",
            "Control + L")

    def test_docbook_variablelist(self):
        self.check(
            '<variablelist role="params">\n\t  <varlistentry>\n\t    <term><parameter>chooser</parameter>&nbsp;:</term>\n\t    <listitem>\n\t      <simpara>\n\t\tthe object which received the signal.\n\t      </simpara>\n\t    </listitem>\n\t  </varlistentry>\n\t  <varlistentry>\n\t    <term><parameter>path</parameter>&nbsp;:</term>\n\t    <listitem>\n\t      <simpara>\n\t\tdefault contents for the text entry for the file name\n\t      </simpara>\n\t    </listitem>\n\t  </varlistentry>\n\t  <varlistentry>\n\t    <term><parameter>user_data</parameter>&nbsp;:</term>\n\t    <listitem>\n\t      <simpara>\n\t\tuser data set when the signal handler was connected.\n\t      </simpara>\n\t    </listitem>\n\t  </varlistentry>\n\t</variablelist>',
            """

chooser\\:
    the object which received the signal.


path\\:
    default contents for the text entry for the file name


user\\_data\\:
    user data set when the signal handler was connected.\
""")

    def test_varlistentry(self):
        self.check(
            "<varlistentry><term>#POPPLER_ANNOT_TEXT_ICON_NOTE</term></varlistentry>",
            "\n#POPPLER\\_ANNOT\\_TEXT\\_ICON\\_NOTE")

    def test_markdown_references(self):
        self.check(
            "a [foo][bar] b [quux][baz]",
            "a 'foo [bar]' b 'quux [baz]'")

        self.check(
            "a [foo][AtkObject]",
            "a :obj:`Atk.Object`")

        self.check(
            "a [foo][im-a-ref]",
            "a `foo <http://example.com>`__")

        self.check(
            "a [foo][gtk-tree-model-get]",
            "a :obj:`Gtk.TreeModel.get`")

        self.check(
            "a [foo][GtkContainer--border-width]",
            "a :obj:`Gtk.Container.props.border_width`")

    def test_markdown_literal(self):
        self.check(
            "`bla[0][1] = 3`",
            "``bla[0][1] = 3``")

        self.check(
            "`<sadaf>`",
            "``<sadaf>``")

    def test_vfuncs(self):
        self.check(
            "#GtkWidget.get_request_mode()",
            ":obj:`Gtk.Widget.do_get_request_mode`\\()")

    def test_various(self):

        self.check("foo <bar> bla <baz> g", "foo <bar> bla <baz> g")

        self.check(
            "appropriate.  #AtkTable summaries may themselves be (simplified) #AtkTables, etc.",
            "appropriate.  :obj:`Atk.Table` summaries may themselves be (simplified) :obj:`Atk.Tables <Atk.Table>`, etc.")

        self.check(
            "02:30 on March 14th 2010",
            "02\\:30 on March 14th 2010",
            "Gtk.Widget")

    def test_markdown_code(self):
        self.check(
            """\
|[<!-- language="C" -->
    GdkEvent *event;
    GdkEventType type;

    type = event->type;
]|
""",
            """
.. code-block:: c

    GdkEvent *event;
    GdkEventType type;
    
    type = event->type;
""")
