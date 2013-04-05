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
import inspect
import subprocess
import shutil

NAMESPACE = ""
VERSION = ""


TYPES = {}

PARAMETERS = {}
RETURNS = {}
FUNCTIONS = {}
CLASSES = {}


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
                local = namespace + "." + local
            return ":class:`%s` " % local
        return x
    d = re.sub('#([A-Za-z]*)', fixup_class_refs, d)
    d = re.sub('%([A-Za-z0-9_]*)', fixup_class_refs, d)

    def fixup_param_refs(match):
        return "`%s`" % match.group(1)
    d = re.sub('@([A-Za-z0-9_]*)', fixup_param_refs, d)

    def fixup_function_refs(match):
        x = match.group(1)
        if x in TYPES:
            return ":func:`%s`" % TYPES[x]
        return x
    d = re.sub('([a-z0-9_]+)\(\)', fixup_function_refs, d)

    d = d.replace("NULL", ":obj:`None`")
    d = d.replace("%NULL", ":obj:`None`")
    d = d.replace("%TRUE", ":obj:`True`")
    d = d.replace("TRUE", ":obj:`True`")
    d = d.replace("%FALSE", ":obj:`False`")
    d = d.replace("FALSE", ":obj:`False`")
    return d


def init():
    gir_path = "/usr/share/gir-1.0/%s-%s.gir" % (NAMESPACE, VERSION)

    handle = open(gir_path, "rb")
    data = handle.read()
    handle.close()

    dom = parseString(data)

    # get a mapping of inline references and real classes
    for t in dom.getElementsByTagName("type"):
        local_name = t.getAttribute("name")
        c_name = t.getAttribute("c:type").rstrip("*")
        TYPES[c_name] = local_name

    # gtk_main -> Gtk.main
    for t in dom.getElementsByTagName("function"):
        local_name = t.getAttribute("name")
        namespace = t.parentNode.getAttribute("name")
        c_name = t.getAttribute("c:identifier")
        name = namespace + "." + local_name
        TYPES[c_name] = name

    for t in dom.getElementsByTagName("member"):
        parent = t.parentNode
        if parent.tagName == "bitfield" or parent.tagName == "enumeration":
            c_name = t.getAttribute("c:identifier")
            local_name = NAMESPACE + "." + parent.getAttribute("name") + "." + t.getAttribute("name").upper()
            TYPES[c_name] = local_name

    for doc in dom.getElementsByTagName("doc"):
        parent = doc.parentNode
        docs = fixup_docs(NAMESPACE, doc.firstChild.nodeValue)

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
        elif parent_name == "class":
            local_name = parent.getAttribute("name")
            CLASSES[local_name] = docs


def import_namespace(namespace, version):
    import pgi
    pgi.install_as_gi()
    import gi
    gi.require_version(namespace, version)
    module = __import__("gi.repository", fromlist=[namespace])
    return getattr(module, namespace)


def parse_class(namespace, name, obj):
    bases = ", ".join(map(lambda x: x.__name__, obj.__bases__))

    docs = CLASSES.get(name, "")

    return """
class %s(object):
    '''
%s
    '''\n""" % (name, docs)


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


class Generator(object):

    def __init__(self, namespace, version):
        # create the basic package structure
        self.prefix = "_%s_%s" % (namespace, version)
        mkdir(self.prefix)
        module_path = os.path.join(self.prefix, namespace + ".py")
        self.module = open(module_path, "wb")


        func_name = "_functions.rst"
        func_path = os.path.join(self.prefix, func_name)
        self.func_handle = open(func_path, "wb")
        self.func_handle.write("""
Functions
=========
""")

        class_name = "_classes.rst"
        class_path = os.path.join(self.prefix, class_name)
        self.class_handle = open(class_path, "wb")
        self.class_handle.write("""
Classes
=======
""")

        # utf-8 encoded .py
        self.module.write("# -*- coding: utf-8 -*-\n")

    def add_function(self, name, code):
        """Add a function"""

        if not isinstance(code, str):
            code = code.encode("utf-8")

        self.module.write(code)
        h = self.func_handle
        h.write(".. autofunction:: %s\n\n" % name)

    def add_class(self, name, code):
        """Add a class"""

        if not isinstance(code, str):
            code = code.encode("utf-8")

        self.module.write(code)
        h = self.class_handle
        h.write(".. autoclass:: %s\n\n" % name)

    def finalize(self):
        func_name = os.path.basename(self.func_handle.name)
        class_name = os.path.basename(self.class_handle.name)

        with open(os.path.join(self.prefix, "index.rst"),  "wb") as h:
            title = "Python - %s %s - API Documentation" % (NAMESPACE, VERSION)
            h.write(title + "\n")
            h.write(len(title) * "=" + "\n")

            h.write("""

.. toctree::
    %(functions)s
    %(classes)s

""" % {"functions": func_name, "classes": class_name})

        self.func_handle.close()
        self.class_handle.close()
        self.module.close()

        dest_conf = os.path.join(self.prefix, "conf.py")
        build_dir = os.path.join(self.prefix, "_build")
        shutil.copy("conf.py", dest_conf)
        theme_dest = os.path.join(self.prefix, "minimalism")
        shutil.copytree("minimalism", theme_dest)
        subprocess.call(["sphinx-build", self.prefix, build_dir])


def create_docs(namespace, version):
    gen = Generator(namespace, version)
    mod = import_namespace(namespace, version)

    for key in dir(mod):
        if key.startswith("_"):
            continue
        obj = getattr(mod, key)

        name = "%s.%s" % (namespace, key)

        if isinstance(obj, types.FunctionType):
            code = parse_method(namespace, key, obj)
            if code:
                gen.add_function(name, code)
        elif inspect.isclass(obj):
            code = parse_class(namespace, key, obj)
            if code:
                gen.add_class(name, code)
        else:
            continue

    gen.finalize()


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print "%s <NAMESPACE> <VERSION>" % sys.argv[0]
        raise SystemExit(1)

    NAMESPACE, VERSION = sys.argv[1:]

    init()
    create_docs(NAMESPACE, VERSION)
