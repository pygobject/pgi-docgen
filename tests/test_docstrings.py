# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import unittest

from pgidocgen.repo import docstring_to_rest
from pgidocgen.namespace import get_base_types


class TDocstring(unittest.TestCase):

    def setUp(self):
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
        }
        self.types.update(get_base_types())

        self.docrefs = {
            "im-a-ref": "http://example.com",
        }

        self.type_structs = {
            "GtkWidgetClass": "Gtk.Widget",
        }

    def get_docrefs(self):
        return self.docrefs

    def get_types(self):
        return self.types

    def get_type_structs(self):
        return self.type_structs

    def _check(self, text, expected):
        out = docstring_to_rest(self, "Gtk.Widget", text)
        self.assertEqual(out, expected)

    def test_various(self):
        data = [(
            "%TRUE foo bar, %FALSE bar.",
            ":obj:`True` foo bar, :obj:`False` bar.",
        ),(
            "a #GQuark id to identify the data",
            "a :obj:`GLib.Quark` id to identify the data",
        ),(
            "g_rand_new_with_seed()",
            ":obj:`GLib.Rand.new_with_seed` ()",
        ),(
            "The GTypeInterface structure",
            "The :obj:`GObject.TypeInterface` structure",
        ),(
            "%TRUE if g_value_copy() with @src_type and @dest_type.",
            ":obj:`True` if :obj:`GObject.Value.copy` () with `src_type` and `dest_type`.",
        ),(
            "To free this list, you can use |[ g_slist_free_full (list, (GDestroyNotify) g_object_unref); ]|",
            "To free this list, you can use ``g_slist_free_full (list, (GDestroyNotify) g_object_unref);``",
        ),(
            "target attribute on &lt;a&gt; elements.",
            "target attribute on <a> elements.",
        ),(
            """\
Retrieves the current length of the text in
@entry. 

This is equivalent to:

<informalexample><programlisting>
gtk_entry_buffer_get_length (gtk_entry_get_buffer (entry));
</programlisting></informalexample>\
""",
            """\
Retrieves the current length of the text in
`entry`. 

This is equivalent to\\:

``gtk_entry_buffer_get_length (gtk_entry_get_buffer (entry));``\
""",
        ),(
            "the unique ID for @window, or <literal>0</literal> if the window has not yet been added to a #GtkApplication",
            "the unique ID for `window`, or ``0`` if the window has not yet been added to a :obj:`Gtk.Application`",
        ),(
            "This is called for each unknown element under &lt;child&gt;.",
            "This is called for each unknown element under <child>."
        ),(
            "GQuark",
            ":obj:`GLib.Quark`"
        ),(
            "@icon_set.",
            "`icon_set`.",
        ),(
            "Emits the #GtkCellEditable::editing-done signal.",
            "Emits the :obj:`Gtk.CellEditable` :py:func:`::editing-done<Gtk.CellEditable.signals.editing_done>` signal.",
        ),(
            "Returns the value of the ::columns signal.",
            "Returns the value of the :py:func:`::columns<Gtk.Widget.signals.columns>` signal.",
        ),(
            "a filename or %NULL",
            "a filename or :obj:`None`",
        ),(
            "%TRUE if @page is complete.",
            ":obj:`True` if `page` is complete.",
        ),(
            "always returns %FALSE.",
            "always returns :obj:`False`."
        ),(
            "you would\nwrite: <literal>;gtk_tree_model_get (model, iter, 0, &amp;place_string_here, -1)</literal>,\nwhere <literal>place_string_here</literal> is a <type>gchar*</type>\nto be filled with the string.",
            "you would\nwrite\\: ``;gtk_tree_model_get (model, iter, 0, &place_string_here, -1)``,\nwhere ``place_string_here`` is a ``gchar*``\nto be filled with the string.",
        ),(
            "Please note\nthat @GTK_TREE_VIEW_COLUMN_AUTOSIZE are inefficient",
            "Please note\nthat :obj:`Gtk.TreeViewColumnSizing.AUTOSIZE` are inefficient"
        ),(
            "the NULL state or initial state",
            "the :obj:`None` state or initial state"
        ),(
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
"""
        ),(
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
* :obj:`Gtk.Widget.do_get_request_mode` ()
* :obj:`Gtk.Widget.do_get_preferred_width` ()
* :obj:`Gtk.Widget.do_get_preferred_height` ()
* :obj:`Gtk.Widget.do_get_preferred_height_for_width` ()
* :obj:`Gtk.Widget.do_get_preferred_width_for_height` ()
* :obj:`Gtk.Widget.do_get_preferred_height_and_baseline_for_width` ()
"""
),(
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
"""
    ,
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
"""
),(
        """\
foo,
bar.

foo,
bar.

foo,
bar.
""",
        """\
foo,
bar.

foo,
bar.

foo,
bar.
""",
),(
            "the #AtkTextAttribute enumerated type corresponding to the specified name, or #ATK_TEXT_ATTRIBUTE_INVALID if no matching text attribute is found.",
            "the :obj:`Atk.TextAttribute` enumerated type corresponding to the specified name, or #ATK\\_TEXT\\_ATTRIBUTE\\_INVALID if no matching text attribute is found."
),(
        "a |[ blaa()\n ]| adsad",
        "a ``blaa()`` adsad",
),(
        "or #ATK_RELATION_NULL if",
        "or :obj:`Atk.RelationType.NULL` if"
),(
        "table by initializing **selected",
        "table by initializing \\*\\*selected",
),(
        "captions are #AtkObjects",
        "captions are :obj:`Atk.Objects <Atk.Object>`"
),(
        "appropriate.  #AtkTable summaries may themselves be (simplified) #AtkTables, etc.",
        "appropriate.  :obj:`Atk.Table` summaries may themselves be (simplified) :obj:`Atk.Tables <Atk.Table>`, etc.",
),(
        "the #GtkSettings:gtk-error-bell setting",
        "the :obj:`Gtk.Settings` :py:data:`:gtk-error-bell<Gtk.Settings.props.gtk_error_bell>` setting",
),(
        "implementing a #GtkContainer: a",
        "implementing a :obj:`Gtk.Container`: a",
),(
        "returns a gint*.",
        "returns a :obj:`int`."
),(
        "a #gint** that",
        "a :obj:`int` that"
),(
        "Since: this is",
        "Since\\: this is",
),(
        "foo #GdkFrameTiming",
        "foo :obj:`Gdk.FrameTiming <Gdk.FrameTimings>`",
),(
        "%NULL-terminated",
        ":obj:`None`-terminated",  # kinda useless, but hey
),(
        "returns a #gpointer",
        "returns a :obj:`object`"
),(
        "<keycombo><keycap>Control</keycap><keycap>L</keycap></keycombo>",
        "Control + L",
),(
        '<variablelist role="params">\n\t  <varlistentry>\n\t    <term><parameter>chooser</parameter>&nbsp;:</term>\n\t    <listitem>\n\t      <simpara>\n\t\tthe object which received the signal.\n\t      </simpara>\n\t    </listitem>\n\t  </varlistentry>\n\t  <varlistentry>\n\t    <term><parameter>path</parameter>&nbsp;:</term>\n\t    <listitem>\n\t      <simpara>\n\t\tdefault contents for the text entry for the file name\n\t      </simpara>\n\t    </listitem>\n\t  </varlistentry>\n\t  <varlistentry>\n\t    <term><parameter>user_data</parameter>&nbsp;:</term>\n\t    <listitem>\n\t      <simpara>\n\t\tuser data set when the signal handler was connected.\n\t      </simpara>\n\t    </listitem>\n\t  </varlistentry>\n\t</variablelist>',
        """

chooser\\:
    the object which received the signal.


path\\:
    default contents for the text entry for the file name


user\\_data\\:
    user data set when the signal handler was connected.\
""",
),(
        "<varlistentry><term>#POPPLER_ANNOT_TEXT_ICON_NOTE</term></varlistentry>",
        "\n#POPPLER\\_ANNOT\\_TEXT\\_ICON\\_NOTE",
),(
        "this is some ::signal-foo blah",
        "this is some :py:func:`::signal-foo<Gtk.Widget.signals.signal_foo>` blah",
),(
        "unless it has handled or blocked `SIGPIPE'.",
        "unless it has handled or blocked \\`SIGPIPE'.",
),(
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


.. code-block:: c

    foo;
    bar;

bar\
""",
),(
        "a style class named <literal>level-</literal>@name",
        "a style class named ``level-`` `name`",
),(
        "a [foo][bar] b [quux][baz]",
        "a 'foo [bar]' b 'quux [baz]'",
),(
        "a [foo][AtkObject]",
        "a :obj:`Atk.Object`",
),(
        "a [foo][im-a-ref]",
        "a `foo <http://example.com>`__",
),(
        "a [foo][gtk-tree-model-get]",
        "a :obj:`Gtk.TreeModel.get`",
),(
        "a [foo][GtkContainer--border-width]",
        "a :obj:`Gtk.Container.props.border_width`",
),(
        "`bla[0][1] = 3`",
        "``bla[0][1] = 3``",
),(
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
""",
),(
        "in *@dest_x and ",
        "in `dest_x` and ",
        )]

        for in_, out in data:
            self._check(in_, out)
