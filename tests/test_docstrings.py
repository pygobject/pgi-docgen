# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import unittest

from pgidocgen.repo import docstring_to_rest


class TDocstring(unittest.TestCase):

    def setUp(self):
        self.types = {
            "g_rand_new_with_seed": "GLib.Rand.new_with_seed",
            "GQuark": "GLib.Quark",
            "GTypeInterface": "GObject.TypeInterface",
            "g_value_copy": "GObject.Value.copy",
            "GtkCellEditable": "Gtk.CellEditable",
            "gtk_tree_model_get": "Gtk.TreeModel.get",
            "GTK_TREE_VIEW_COLUMN_AUTOSIZE": "Gtk.TreeViewColumnSizing.AUTOSIZE",
            "AtkTextAttribute": "Atk.TextAttribute",
            "ATK_TEXT_ATTR_INVALID": "Atk.TextAttribute.INVALID",
        }

    def _check(self, text, expected, namespace="Default"):
        out = docstring_to_rest(self.types, namespace, text)
        self.assertEqual(out, expected)

    def test_various(self):
        data = [(
            "%TRUE foo bar, %FALSE bar.",
            ":obj:`True` foo bar, :obj:`False` bar.",
        ),(
            "a #GQuark id to identify the data",
            "a :class:`GLib.Quark`  id to identify the data",
        ),(
            "g_rand_new_with_seed()",
            ":class:`GLib.Rand.new_with_seed` ()",
        ),(
            "The GTypeInterface structure",
            "The :class:`GObject.TypeInterface`  structure",
        ),(
            "%TRUE if g_value_copy() with @src_type and @dest_type.",
            ":obj:`True` if :class:`GObject.Value.copy` () with `src_type` and `dest_type`.",
        ),(
            "To free this list, you can use |[ g_slist_free_full (list, (GDestroyNotify) g_object_unref); ]|",
            "To free this list, you can use ",
        ),(
            "target attribute on &lt;a&gt; elements.",
            "target attribute on  elements.",
        ),(
            """\
Retrieves the current length of the text in
@entry. 

This is equivalent to:

<informalexample><programlisting>
gtk_entry_buffer_get_length (gtk_entry_get_buffer (entry));
</programlisting></informalexample>\
""",
            "Retrieves the current length of the text in\n`entry`. \n\nThis is equivalent to:\n\n",
        ),(
            "the unique ID for @window, or <literal>0</literal> if the window has not yet been added to a #GtkApplication",
            "the unique ID for `window`, or `0` if the window has not yet been added to a GtkApplication",
        ),(
            "This is called for each unknown element under &lt;child&gt;.",
            "This is called for each unknown element under ."
        ),(
            "GQuark",
            ":class:`GLib.Quark` "
        ),(
            "@icon_set.",
            "`icon_set`.",
        ),(
            "Emits the #GtkCellEditable::editing-done signal.",
            "Emits the :class:`Gtk.CellEditable`  :ref:`\\:\\:editing-done <editing-done>`  signal.",
        ),(
            "Returns the value of the ::columns property.",
            "Returns the value of the  :ref:`\\:\\:columns <columns>`  property.",
        ),(
            "The cell is in a row that can be expanded. Since 3.4",
            "The cell is in a row that can be expanded. \n\n.. versionadded:: 3.4\n"
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
            "you would\nwrite: &lt;literal&gt;gtk_tree_model_get (model, iter, 0, &amp;amp;place_string_here, -1)&lt;/literal&gt;,\nwhere &lt;literal&gt;place_string_here&lt;/literal&gt; is a &lt;type&gt;gchar*&lt;/type&gt;\nto be filled with the string.",
            "you would\nwrite: `:class:`Gtk.TreeModel.get`  (model, iter, 0, &amp;place_string_here, -1)`,\nwhere `place_string_here` is a gchar*\nto be filled with the string.",
        ),(
            "Please note\nthat @GTK_TREE_VIEW_COLUMN_AUTOSIZE are inefficient",
            "Please note\nthat @:class:`Gtk.TreeViewColumnSizing.AUTOSIZE`  are inefficient"
        ),(
            "the NULL state or initial state",
            "the :obj:`None` state or initial state"
        ),(
            """\
&lt;itemizedlist&gt;
  &lt;listitem&gt;#GtkWidgetClass.get_request_mode()&lt;/listitem&gt;
  &lt;listitem&gt;#GtkWidgetClass.get_preferred_width()&lt;/listitem&gt;
  &lt;listitem&gt;#GtkWidgetClass.get_preferred_height()&lt;/listitem&gt;
  &lt;listitem&gt;#GtkWidgetClass.get_preferred_height_for_width()&lt;/listitem&gt;
  &lt;listitem&gt;#GtkWidgetClass.get_preferred_width_for_height()&lt;/listitem&gt;
  &lt;listitem&gt;#GtkWidgetClass.get_preferred_height_and_baseline_for_width()&lt;/listitem&gt;
&lt;/itemizedlist&gt;\
""",
            """\

  GtkWidgetClass.get_request_mode()
  GtkWidgetClass.get_preferred_width()
  GtkWidgetClass.get_preferred_height()
  GtkWidgetClass.get_preferred_height_for_width()
  GtkWidgetClass.get_preferred_width_for_height()
  GtkWidgetClass.get_preferred_height_and_baseline_for_width()
\
"""
),(
            "the #AtkTextAttribute enumerated type corresponding to the specified name, or #ATK_TEXT_ATTRIBUTE_INVALID if no matching text attribute is found.",
            "the :class:`Atk.TextAttribute`  enumerated type corresponding to the specified name, or ATK_TEXT_ATTRIBUTE_INVALID if no matching text attribute is found."
        )]

        for in_, out in data:
            self._check(in_, out)
