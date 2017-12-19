# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re

from lxml import etree
from xml.sax.saxutils import escape
from bs4 import BeautifulSoup, Tag

from . import util
from .util import escape_rest, force_unindent
from .gtkdoc import ConvertMarkDown
from .docbook_escape import docbook_escape


_scanner = re.Scanner([
    (r"\*?@[A-Za-z0-9_]+", lambda scanner, token:("PARAM", token)),
    (r"[#%]?[A-Za-z0-9_:\-]+\.[A-Za-z0-9_:\-]+\(\)", lambda scanner, token:("VFUNC", token)),
    (r"[#%]?[A-Za-z0-9_:\-]+\.[A-Za-z0-9_:\-]+", lambda scanner, token:("FIELD", token)),
    (r"[#%]?[A-Za-z_]+[A-Za-z0-9_]*::[A-Za-z\-]+[A-Za-z0-9\-_]*", lambda scanner, token:("FULLSIG", token)),
    (r"::[A-Za-z\-]+[A-Za-z0-9\-_]*", lambda scanner, token:("SIG", token)),
    (r"[#%]?[A-Za-z_]+[A-Za-z0-9_]*:[A-Za-z\-]+[A-Za-z0-9\-_]*", lambda scanner, token:("FULLPROP", token)),
    (r":[A-Za-z\-]+[A-Za-z0-9\-_]*", lambda scanner, token:("PROP", token)),
    (r"[#%]?[A-Za-z0-9_]+\**", lambda scanner, token:("ID", token)),
    (r"\s+", lambda scanner, token:("SPACE", token)),
    (r".", lambda scanner, token:("OTHER", token)),
])


def _handle_data(repo, current_type, current_func, d):
    global _scanner

    results, remainder = _scanner.scan(d)
    assert not remainder, repr(remainder)

    def id_ref(token):
        # possible identifier reference

        # strip pointer
        sub = token.rstrip("*")

        if sub.startswith(("#", "%")):
            sub = sub[1:]

        pytype = repo.lookup_py_id(sub)

        if pytype is not None:
            return ":obj:`%s`" % pytype
        elif token.startswith(("#", "%")):
            if token.endswith("s"):
                # if we are sure it's a reference and it ends with 's'
                # like "a list of #GtkWindows", we also try "#GtkWindow"
                sub = token[1:-1]
                pytype = repo.lookup_py_id(sub)
                if pytype is not None:
                    assert "." in pytype
                    return ":obj:`%s <%s>`" % (pytype + "s", pytype)
            else:
                # also try to add "s", GdkFrameTiming(s)
                sub = token[1:] + "s"
                pytype = repo.lookup_py_id(sub)
                if pytype is not None:
                    py_no_s = pytype[:-1] if pytype[-1] == "s" else pytype
                    return ":obj:`%s <%s>`" % (py_no_s, pytype)

        return token

    out = []
    need_space_at_start = False
    for type_, token in results:
        orig_token = token
        if type_ == "PARAM":
            token = token.lstrip("*")
            # paremeter reference
            assert token[0] == "@"
            token = token[1:]
            if token.upper() == token:
                # some docs use it to reference constants..
                token = id_ref(token)
            else:
                if current_func is not None:
                    instance_param = repo.lookup_instance_param(current_func)
                    if token == instance_param:
                        token = "self"
                token = "`%s`" % token
        elif type_ == "VFUNC":
            assert token[-2:] == "()"
            vfunc = token[:-2]
            if vfunc.startswith(("#", "%")):
                vfunc = vfunc[1:]
            class_id, field = vfunc.split(".", 1)
            pytype = repo.lookup_py_id_for_type_struct(class_id)
            if pytype is None:
                # fall back to the class, for #GObject.constructed()
                pytype = repo.lookup_py_id(class_id)
            if pytype is not None:
                token = ":obj:`%s.do_%s`\\()" % (pytype, field)
        elif type_ == "FIELD":
            field = token
            if field.startswith(("#", "%")):
                field = field[1:]
            c_id, field_name = field.split(".", 1)
            objtype = repo.lookup_py_id(c_id)
            if objtype is not None:
                token = ":ref:`%s.%s <%s.fields>`" % (
                    objtype, field_name, objtype)
        elif type_ == "FULLPROP" or type_ == "PROP":
            c_id, prop_name = token.split(":")
            if c_id.startswith(("#", "%")):
                c_id = c_id[1:]

            if not c_id:
                py_id = current_type
            else:
                py_id = repo.lookup_py_id(c_id)

            if py_id and "_" not in prop_name:
                prop_attr = prop_name.replace("-", "_")

                token = id_ref(c_id)
                if token:
                    token += " "

                rst_target = py_id + ".props." + prop_attr
                token += ":py:data:`:%s<%s>`" % (
                    prop_name, rst_target)
        elif type_ == "FULLSIG" or type_ == "SIG":
            c_id, sig_name = token.split("::")
            if c_id.startswith(("#", "%")):
                c_id = c_id[1:]

            # Some docs use GtkWidegetClass::foo to reference vfuncs. We
            # can skip them when we find out that it is a type struct as they
            # can't have signals
            is_type_struct = bool(repo.lookup_py_id_for_type_struct(c_id))

            if not c_id:
                py_id = current_type
            else:
                py_id = repo.lookup_py_id(c_id)

            if py_id and "_" not in sig_name and not is_type_struct:
                sig_attr = sig_name.replace("-", "_")

                token = id_ref(c_id)
                if token:
                    token += " "

                rst_target = py_id + ".signals." + sig_attr
                token += ":py:func:`::%s<%s>`" % (
                    sig_name, rst_target)
        elif type_ == "ID":
            token = id_ref(token)

        changed = orig_token != token

        # nothing changed, escape
        if not changed:
            token = escape_rest(token)

        # insert a space for the previous one
        if need_space_at_start:
            if not token:
                pass
            else:
                if not token.startswith((" ", "\\", ",", ".", ":", "-", "\n", ")")):
                    if changed:
                        token = " " + token
                    else:
                        token = "\\" + token
                need_space_at_start = False

        if changed and token and escape_rest(token[-1]) != token[-1]:
            # something changed, we have to make sure that
            # the previous and next character is a space so
            # docutils doesn't get confused wit references
            need_space_at_start = True

        out.append(token)

    return "".join(out)


def docref_to_pyref(repo, ref, text):
    """Take a gtk-doc reference and try to convert it to a Python reference.

    If that fails returns None.
    """

    # GtkEntryCompletion
    pyref = repo.lookup_py_id(ref)
    if pyref is not None:
        # if the link text is a C type, try to convert it
        textref = repo.lookup_py_id(text)
        if not textref:
            textref = escape_rest(text)
        if textref != pyref:
            return ":obj:`%s <%s>`" % (textref, pyref)
        else:
            return ":obj:`%s`" % pyref

    # gtk-assistant-commit -> gtk_assistant_commit -> Gtk.Assistant.commit
    func = ref.replace("-", "_")
    pyref = repo.lookup_py_id(func)
    if pyref is not None:
        return ":obj:`%s <%s>`" % (escape_rest(text), pyref)

    # GtkEntryCompletion--inline-completion ->
    #   Gtk.EntryCompletion.props.inline_completion
    if "--" in ref:
        type_, prop = ref.split("--", 1)
        prop = prop.replace("-", "_")
        pyref = repo.lookup_py_id(type_)
        if pyref is not None:
            return ":obj:`%s <%s.props.%s>`" % (escape_rest(text), pyref, prop)

    return None


def _handle_xml(repo, current_type, current_func, out, item):

    def handle_next(out, item):
        return _handle_xml(repo, current_type, current_func, out, item)

    def handle_data(text):
        return _handle_data(repo, current_type, current_func, text)

    if isinstance(item, Tag):
        item_text = item.getText().strip()
        if item.name == "literal" or item.name == "type":
            if item.text:
                # docutils doesn't like empty literals..
                out.append("``%s``" % item.text)
        elif item.name == "itemizedlist":
            lines = []
            for item in item.contents:
                if not isinstance(item, Tag):
                    continue
                other_out = []
                handle_next(other_out, item)
                item_text = "".join(other_out).strip()
                data = ""
                for i, line in enumerate(item_text.splitlines()):
                    if i == 0:
                        data += "* " + line + "\n"
                    else:
                        data += "  " + line + "\n"
                lines.append(data.rstrip())
            out.append("\n" + "\n".join(lines) + "\n")
        elif item.name == "ulink":
            out.append("`%s <%s>`__" % (item_text, item.get("url", "")))
        elif item.name == "link":
            lines = []
            linked = item.get("linkend", "")
            if not linked:
                lines.append(item_text)
            else:
                pyref = docref_to_pyref(repo, linked, item_text)
                if pyref is not None:
                    lines.append(pyref)
                else:
                    url = repo.lookup_gtkdoc_ref(linked)
                    if url is not None:
                        lines.append("`%s <%s>`__" % (item_text, url))
                    else:
                        lines.append("'%s [%s]'" % (item_text, linked))
                        repo.missed_links += 1
            out.extend(lines)
        elif item.name == "programlisting" or item.name == "screen":
            if not item_text.count("\n"):
                out.append("``%s``" % item_text)
            else:
                language = item.get("language", "none").lower()
                code = "\n.. code-block:: %s\n\n%s\n" % (
                    language,
                    util.indent(
                        util.unindent(item_text, ignore_first_line=True)))
                out.append(code)
        elif item.name == "para":
            for item in item.contents:
                handle_next(out, item)
            out.append("\n")
        elif item.name == "title":
            # fake a title by creating a "Definition List". It can contain
            # inline markup and is bold in the default theme. Only restriction
            # is it doesn't allow newlines, but we can live with that for
            # titles
            title_text = " ".join(
                handle_data(item_text).splitlines())
            code = "\n%s\n    ..\n        .\n\n" % title_text
            out.append(code)
        elif item.name == "keycombo":
            subs = []
            for sub in item.contents:
                if not isinstance(sub, Tag):
                    continue
                subs.append(handle_data(sub.getText().strip()))
            out.append(" + ".join(subs))
        elif item.name == "varlistentry":
            terms = []
            listitem = None
            for sub in item.contents:
                if not isinstance(sub, Tag):
                    continue

                if sub.name == "term":
                    terms.append(sub.getText().strip())
                elif sub.name == "listitem":
                    listitem = sub.getText().strip()
                else:
                    assert 0

            # Poppler-0.18
            if not listitem:
                listitem = ""

            assert terms

            lines = []
            terms_line = ", ".join(
                [handle_data(t) for t in terms])
            lines.append("%s\n" % terms_line)
            listitem = force_unindent(listitem, ignore_first_line=True)
            lines.append(
                util.indent(handle_data(listitem)) + "\n")
            out.append("\n")
            out.extend(lines)
        else:
            for sub in item.contents:
                handle_next(out, sub)
    else:
        if not out or out[-1].endswith("\n"):
            data = force_unindent(item.string, ignore_first_line=False)
        else:
            data = force_unindent(item.string, ignore_first_line=True)
        out.append(handle_data(data))


def _docstring_to_docbook(docstring):
    """Takes a docstring from the gir and converts the markdown/docbook
    mix to docbook.

    Unlike in gtk-doc references to types/symbols will not be resolved.
    Things like "#GtkWidget" will remain as is.
    """

    docstring = docbook_escape(docstring)
    docstring = ConvertMarkDown("", docstring)

    # ConvertMarkDown doesn't handle inline markup yet... so at least convert
    # inline code for now
    def to_programlisting(match):
        from xml.sax.saxutils import escape
        escaped = escape(match.group(1))
        return "<programlisting>%s</programlisting>" % escaped

    docstring = re.sub("\|\[(.*?)\]\|", to_programlisting,
                       docstring, flags=re.MULTILINE | re.DOTALL)

    return docstring


def _docbook_to_rest(repo, docbook, current_type, current_func):
    dummy = "<dummy>" + docbook + "</dummy>"
    dummy = etree.tostring(
        etree.fromstring(dummy, parser=etree.XMLParser(recover=True)))
    soup = BeautifulSoup(dummy, "xml")

    out = []
    for item in soup.contents:
        _handle_xml(repo, current_type, current_func, out, item)

    # make sure to insert spaces between special reST chars
    rst = ""
    while out:
        c = out.pop(0)
        if rst and c:
            last = rst[-1]
            first = c[0]
            if escape_rest(last) != last and escape_rest(first) != first:
                rst += " "
        rst += c

    return rst


def docstring_to_rest(repo, docstring, current_type=None, current_func=None):
    """Converts `docstring` to reST.

    Args:
        repo (Repository): the repo that produced the docstring
        docstring (str): the docstring
        current_type (str or None): the Python identifier for the docstring.
            In case the docstring comes from Gtk.Widget.some_func, the parser
            can use "Gtk.Widget" in case a signal without a class name is
            referenced.
        current_func (str or None): The Python identifier for the docstring.
            In case the docstring comes from Gtk.Widget.some_func, the parser
            can use "Gtk.Widget.some_func" to rewrite instance parameters.

    Returns:
        str: the docstring converted to reST
    """

    if current_type is not None:
        # types
        assert current_type.count(".") == 1

    if current_func is not None:
        # functions or methods
        assert current_func.count(".") in (1, 2)

    def esc_xml(text):
        # in case it's not valid xml, assume markdown and escape
        try:
            etree.tostring(etree.fromstring(
                "<dummy>%s</dummy>" % text.replace(
                    "&nbsp;", "&#160;")))
        except etree.XMLSyntaxError as e:
            text = escape(text)
        return text

    # skip inline code when escaping xml
    reg = re.compile("(\|\[.*?\]\|)", flags=re.MULTILINE | re.DOTALL)
    docstring = "".join([
        p if reg.match(p) else esc_xml(p) for p in reg.split(docstring)])

    docbook = _docstring_to_docbook(docstring)
    rst = _docbook_to_rest(repo, docbook, current_type, current_func)

    if not docstring.endswith("\n"):
        rst = rst.rstrip("\n")
    while rst.endswith("\n\n"):
        rst = rst[:-1]

    return rst
