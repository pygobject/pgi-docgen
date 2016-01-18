# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re

from BeautifulSoup import BeautifulStoneSoup, Tag

from . import util
from .util import escape_rest, force_unindent
from .gtkdoc import ConvertMarkDown


def _handle_data(repo, current_type, current_func, d):

    scanner = re.Scanner([
        (r"\*?@[A-Za-z0-9_]+", lambda scanner, token:("PARAM", token)),
        (r"[#%]?[A-Za-z0-9_:\-]+\.[A-Za-z0-9_:\-]+\(\)", lambda scanner, token:("VFUNC", token)),
        (r"[#%]?[A-Za-z0-9_:\-]+\**", lambda scanner, token:("ID", token)),
        (r"\(", lambda scanner, token:("OTHER", token)),
        (r"\)", lambda scanner, token:("OTHER", token)),
        (r",", lambda scanner, token:("OTHER", token)),
        (r"\s", lambda scanner, token:("SPACE", token)),
        (r"[^\s]+", lambda scanner, token:("OTHER", token)),
    ])

    results, remainder = scanner.scan(d)
    assert not remainder

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
                token = ":obj:`%s.do_%s` ()" % (pytype, field)
        elif type_ == "ID":
            parts = re.split("(::?)", token)
            fallback = True
            if len(parts) > 2:
                obj, sep, sigprop = parts[0], parts[1], "".join(parts[2:])
                obj_id = obj.lstrip("#")
                objtype = repo.lookup_py_id(obj_id)
                if objtype is not None:
                    obj_rst_id = objtype
                elif current_type:
                    obj_rst_id = ".".join(current_type.split(".")[:2])
                else:
                    obj_rst_id = None

                if sigprop and obj_rst_id:
                    fallback = False
                    token = id_ref(obj)
                    is_prop = len(sep) == 1

                    if token:
                        token += " "

                    prop_name = sigprop.replace("_", "-")
                    prop_attr = sigprop.replace("-", "_")
                    if is_prop:
                        rst_target = obj_rst_id + ".props." + prop_attr
                        token += ":py:data:`:%s<%s>`" % (
                            prop_name, rst_target)
                    else:
                        rst_target = obj_rst_id + ".signals." + prop_attr
                        token += ":py:func:`::%s<%s>`" % (
                            prop_name, rst_target)

            if fallback:
                if "-" in token:
                    first, rest = token.split("-", 1)
                    token = id_ref(first) + "-" + rest
                elif token.endswith(":"):
                    token = id_ref(token[:-1]) + ":"
                else:
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
                # ., is also OK
                if not token.startswith((" ", ".", ",")):
                    token = " " + token
                need_space_at_start = False

        if changed:
            # something changed, we have to make sure that
            # the previous and next character is a space so
            # docutils doesn't get confused wit references
            need_space_at_start = True

        out.append(token)

    return "".join(out)


def docref_to_pyref(repo, ref):
    """Take a gtk-doc reference and try to convert it to a Python reference.

    If that fails returns None.
    """

    # GtkEntryCompletion
    pyref = repo.lookup_py_id(ref)
    if pyref is not None:
        return pyref

    # gtk-assistant-commit -> gtk_assistant_commit -> Gtk.Assistant.commit
    func = ref.replace("-", "_")
    pyref = repo.lookup_py_id(func)
    if pyref is not None:
        return pyref

    # GtkEntryCompletion--inline-completion ->
    #   Gtk.EntryCompletion.props.inline_completion
    if "--" in ref:
        type_, prop = ref.split("--", 1)
        prop = prop.replace("-", "_")
        pyref = repo.lookup_py_id(type_)
        if pyref is not None:
            return "%s.props.%s" % (pyref, prop)

    return None


def _handle_xml(repo, current_type, current_func, out, item):

    def handle_next(out, item):
        return _handle_xml(repo, current_type, current_func, out, item)

    def handle_data(text):
        return _handle_data(repo, current_type, current_func, text)

    if isinstance(item, Tag):
        if item.name == "literal" or item.name == "type":
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
            out.append("`%s <%s>`__" % (item.getText(), item.get("url", "")))
        elif item.name == "link":
            linked = item.get("linkend", "")
            if not linked:
                out.append(item.getText())
            else:
                pyref = docref_to_pyref(repo, linked)
                if pyref is not None:
                    out.append(":obj:`%s`" % pyref)
                else:
                    url = repo.lookup_gtkdoc_ref(linked)
                    if url is not None:
                        out.append("`%s <%s>`__" % (item.getText(), url))
                    else:
                        out.append("'%s [%s]'" % (item.getText(), linked))
        elif item.name == "programlisting":
            text = item.getText()
            if not text.count("\n"):
                out.append("``%s``" % item.getText())
            else:
                code = "\n.. code-block:: c\n\n%s\n" % util.indent(
                    util.unindent(item.getText(), ignore_first_line=True))
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
                handle_data(item.getText()).splitlines())
            code = "\n%s\n    ..\n        .\n\n" % title_text
            out.append(code)
        elif item.name == "keycombo":
            subs = []
            for sub in item.contents:
                if not isinstance(sub, Tag):
                    continue
                subs.append(handle_data(sub.getText()))
            out.append(" + ".join(subs))
        elif item.name == "varlistentry":
            terms = []
            listitem = None
            for sub in item.contents:
                if not isinstance(sub, Tag):
                    continue

                if sub.name == "term":
                    terms.append(sub.getText())
                elif sub.name == "listitem":
                    listitem = sub.getText()
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
    soup = BeautifulStoneSoup(docbook,
                              convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
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

    docbook = _docstring_to_docbook(docstring)
    rst = _docbook_to_rest(repo, docbook, current_type, current_func)

    if not docstring.endswith("\n"):
        rst = rst.rstrip("\n")
    while rst.endswith("\n\n"):
        rst = rst[:-1]

    return rst
