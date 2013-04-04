#!/usr/bin/python
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# this is all ugly.. but a start

import sys
sys.path.insert(0, "../")

from xml.dom.minidom import parseString
import xml.sax.saxutils as saxutils
import types
import os
import re


TYPES = {}
PARAMETERS = {}
RETURNS = {}
FUNCTIONS = {}


def fixup_docs(namespace, d):

    d = saxutils.unescape(d)

    def fixup_code(match):
        code = match.group(1)
        lines = code.splitlines()
        return "\n::\n\n%s" % ("\n".join(["    %s" % l for l in lines]))
    d = re.sub('\|\[(.*?)\]\|', fixup_code, d, flags=re.MULTILINE | re.DOTALL)
    d = re.sub('<programlisting>(.*?)</programlisting>', fixup_code, d, flags=re.MULTILINE | re.DOTALL)

    d = re.sub('<literal>(.*?)</literal>', '`\\1`', d)
    d = re.sub('<[^<]+?>', '', d)

    def fixup_class_refs(match):
        x = match.group(1)
        if x in TYPES:
            local = TYPES[x]
            if "." not in local:
                return ":class:`%s.%s` " % (namespace, local)
            return ":class:`%s` " % local
        return x
    d = re.sub('#([A-Za-z]*)', fixup_class_refs, d)
    d = re.sub('%([A-Za-z0-9_]*)', fixup_class_refs, d)

    def fixup_param_refs(match):
        return "`%s`" % match.group(1)
    d = re.sub('@([A-Za-z0-9_]*)', fixup_param_refs, d)

    d = d.replace("NULL", ":obj:`None`")
    d = d.replace("%NULL", ":obj:`None`")
    d = d.replace("%TRUE", ":obj:`True`")
    d = d.replace("TRUE", ":obj:`True`")
    d = d.replace("%FALSE", ":obj:`False`")
    d = d.replace("FALSE", ":obj:`False`")
    return d


def init():
    # FIXME: hardcoded namespace

    handle = open("/usr/share/gir-1.0/Gtk-3.0.gir", "rb")
    data = handle.read()
    handle.close()

    dom = parseString(data)

    # get a mapping of inline references and real classes
    for t in dom.getElementsByTagName("type"):
        local_name = t.getAttribute("name")
        c_name = t.getAttribute("c:type").rstrip("*")
        TYPES[c_name] = local_name

    for t in dom.getElementsByTagName("member"):
        parent = t.parentNode
        if parent.tagName == "bitfield" or parent.tagName == "enumeration":
            c_name = t.getAttribute("c:identifier")
            local_name = "Gtk" + "." + parent.getAttribute("name") + "." + t.getAttribute("name").upper()
            TYPES[c_name] = local_name

    for doc in dom.getElementsByTagName("doc"):
        parent = doc.parentNode
        docs = fixup_docs("Gtk", doc.firstChild.nodeValue)

        parent_name = parent.tagName
        if parent_name == "parameter":
            up = parent.parentNode.parentNode
            if up.tagName == "function":
                namespace = up.parentNode.getAttribute("name")
                func_name = up.getAttribute("name")
                param_name = parent.getAttribute("name")
                name = namespace + "." + func_name + "." + param_name
                PARAMETERS[name] = docs
        elif parent_name == "function":
            up = parent.parentNode
            if up.tagName == "namespace":
                namespace = up.getAttribute("name")
                func_name = parent.getAttribute("name")
                name = namespace + "." + func_name
                FUNCTIONS[name] = docs
        elif parent_name == "return-value":
            up = parent.parentNode
            if up.tagName == "function":
                namespace = up.parentNode.getAttribute("name")
                func_name = up.getAttribute("name")
                name = namespace + "." + func_name
                RETURNS[name] = docs


def import_namespace(namespace, version):
    import pgi
    pgi.install_as_gi()
    import gi
    gi.require_version(namespace, version)
    module = __import__("gi.repository", fromlist=[namespace])
    return getattr(module, namespace)


def parse_method(namespace, name, obj):
    doc = str(obj.__doc__)
    first_line = doc and doc.splitlines()[0] or ""
    match = re.match("(.*?)\((.*?)\)( -> )?(.*)", first_line)
    if not match:
        return
    groups = match.groups()
    name, args, dummy, ret = groups

    args = args and args.split(",") or []
    args = [a.strip() for a in args]

    ret = ret and ret.split(",") or []

    arg_map = [(a.split(":")[0].strip(), a.split(":")[-1].strip()) for a in args]

    arg_names = ", ".join([a[0] for a in arg_map])
    func_name = namespace + "." + name

    docs = []
    for key, value in arg_map:
        param_key = namespace + "." + name + "." + key
        docs.append(":param %s: %s" % (key, fixup_docs(namespace, PARAMETERS.get(param_key, ""))))
        docs.append(":type %s: :class:`%s`" % (key, value))

    if func_name in RETURNS:
        # don't allow newlines here
        doc_string = " ".join(fixup_docs(namespace, RETURNS[func_name]).splitlines())
        docs.append(":returns:")
        docs.append("    %s" % doc_string)
        if ret:
            docs.append("    , %s" % ", ".join(ret))
    elif ret:
        docs.append(":returns:")
        docs.append("    %s" % ", ".join(ret))

    if func_name in FUNCTIONS:
        docs.append(FUNCTIONS[func_name])

    docs = "\n".join(docs)

    final = """
def %s(%s):
    '''
%s
    '''
""" % (name, arg_names, docs)

    return final


def mkdir(*args):
    try:
        os.mkdir(*args)
    except OSError:
        pass


def create_docs(namespace, version):
    mod = import_namespace(namespace, version)
    mkdir("_generated")
    gi_path = os.path.join("_generated", "gi")
    mkdir(gi_path)
    open(os.path.join(gi_path, "__init__.py"), "wb").close()
    repo_path = os.path.join(gi_path, "repository")
    mkdir(repo_path)
    open(os.path.join(repo_path, "__init__.py"), "wb").close()
    module_path = os.path.join(repo_path, namespace + ".py")

    with open(module_path, "wb") as h:
        for key in dir(mod):
            if key.startswith("_"):
                continue
            obj = getattr(mod, key)

            if isinstance(obj, types.FunctionType):
                func = parse_method(namespace, key, obj)
                if func:
                    h.write(func)


if __name__ == "__main__":
    init()
    create_docs("Gtk", "3.0")
