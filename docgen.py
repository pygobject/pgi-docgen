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


def import_namespace(namespace, version):
    import pgi
    pgi.install_as_gi()
    import gi
    gi.require_version(namespace, version)
    module = __import__("gi.repository", fromlist=[namespace])
    return getattr(module, namespace)


class Namespace(object):
    def __init__(self, name, version):
        self.name = name
        self.version = version

        with open(self.get_path(), "rb") as h:
            self._dom = parseString(h.read())

    def get_path(self):
        return "/usr/share/gir-1.0/%s-%s.gir" % (self.name, self.version)

    def get_dom(self):
        return self._dom

    def get_dependencies(self):
        return []


class Repository(object):

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        # c def name -> python name
        # gtk_foo_bar -> Gtk.foo_bar
        self._types = {}

        # Gtk.foo_bar.arg1 -> "some doc"
        self._parameters = {}

        # Gtk.foo_bar -> "some doc"
        # Gtk.Foo.foo_bar -> "some doc"
        self._functions = {}

        # Gtk.foo_bar -> "some doc"
        # Gtk.Foo.foo_bar -> "some doc"
        self._returns = {}

        # Gtk.FooBar -> "some doc"
        self._classes = {}

        ns = Namespace(namespace, version)
        dom = ns.get_dom()

        self._parse_types(dom)
        self._parse_docs(dom)

    def _parse_types(self, dom):
        """Create a mapping of various C names to python names, taking the
        current namespace into account.
        """

        namespace = self.namespace

        # classes and aliases: GtkFooBar -> Gtk.FooBar
        for t in dom.getElementsByTagName("type"):
            local_name = t.getAttribute("name")
            c_name = t.getAttribute("c:type").rstrip("*")
            self._types[c_name] = local_name

        # gtk_main -> Gtk.main
        for t in dom.getElementsByTagName("function"):
            local_name = t.getAttribute("name")
            namespace = t.parentNode.getAttribute("name")
            c_name = t.getAttribute("c:identifier")
            name = namespace + "." + local_name
            self._types[c_name] = name

        # enums etc. GTK_SOME_FLAG_FOO -> Gtk.SomeFlag.FOO
        for t in dom.getElementsByTagName("member"):
            parent = t.parentNode
            if parent.tagName == "bitfield" or parent.tagName == "enumeration":
                c_name = t.getAttribute("c:identifier")
                class_name = parent.getAttribute("name")
                field_name = t.getAttribute("name").upper()
                local_name = namespace + "." + class_name + "." + field_name
                self._types[c_name] = local_name

    def _parse_docs(self, dom):
        """Parse docs"""

        namespace = self.namespace

        for doc in dom.getElementsByTagName("doc"):
            parent = doc.parentNode
            docs = self._fix(doc.firstChild.nodeValue)
            parent_name = parent.tagName

            if parent_name == "parameter":
                up = parent.parentNode.parentNode
                if up.tagName == "function":
                    if up.parentNode.tagName == "namespace":
                        namespace = up.parentNode.getAttribute("name")
                        func_name = up.getAttribute("name")
                        param_name = parent.getAttribute("name")
                        name = namespace + "." + func_name + "." + param_name
                        self._parameters[name] = docs
                    else:
                        namespace = up.parentNode.parentNode
                        assert namespace.tagName == "namespace"
                        class_ = up.parentNode
                        ns = namespace.getAttribute("name")
                        cls = class_.getAttribute("name")
                        func = up.getAttribute("name")
                        param_name = parent.getAttribute("name")
                        name = ns + "." + cls + "." + func + "." + param_name
                        self._parameters[name] = docs
                elif up.tagName == "method":
                    namespace = up.parentNode.parentNode
                    assert namespace.tagName == "namespace"
                    namespace = namespace.getAttribute("name")
                    owner = up.parentNode.getAttribute("name")
                    method = up.getAttribute("name")
                    param = parent.getAttribute("name")
                    name = namespace + "." + owner + "." + method + "." + param
                    self._parameters[name] = docs
            elif parent_name == "method":
                up = parent.parentNode
                m_owner = up.getAttribute("name")
                namespace = up.parentNode.getAttribute("name")
                method = parent.getAttribute("name")
                name = namespace + "." + m_owner + "." + method
                self._functions[name] = docs
            elif parent_name == "function":
                up = parent.parentNode
                if up.tagName == "namespace":
                    namespace = up.getAttribute("name")
                    func_name = parent.getAttribute("name")
                    name = namespace + "." + func_name
                    self._functions[name] = docs
                elif up.tagName == "class":
                    assert up.parentNode.tagName == "namespace"
                    namespace = up.parentNode.getAttribute("name")
                    class_name = up.getAttribute("name")
                    func_name = parent.getAttribute("name")
                    name = namespace + "." + class_name + "." + func_name
                    self._functions[name] = docs
            elif parent_name == "return-value":
                up = parent.parentNode
                if up.tagName == "function" and \
                        up.parentNode.tagName == "namespace":
                    namespace = up.parentNode.getAttribute("name")
                    func_name = up.getAttribute("name")
                    name = namespace + "." + func_name
                    self._returns[name] = docs
            elif parent_name == "class":
                local_name = parent.getAttribute("name")
                self._classes[local_name] = docs

    def _fix(self, d):

        d = saxutils.unescape(d)

        def fixup_code(match):
            code = match.group(1)
            lines = code.splitlines()
            return "\n::\n\n%s" % ("\n".join(["    %s" % l for l in lines]))

        d = re.sub('\|\[(.*?)\]\|', fixup_code, d,
                   flags=re.MULTILINE | re.DOTALL)
        d = re.sub('<programlisting>(.*?)</programlisting>', fixup_code, d,
                   flags=re.MULTILINE | re.DOTALL)

        d = re.sub('<literal>(.*?)</literal>', '`\\1`', d)
        d = re.sub('<[^<]+?>', '', d)

        def fixup_class_refs(match):
            x = match.group(1)
            if x in self._types:
                local = self._types[x]
                if "." not in local:
                    local = self.namespace + "." + local
                return ":class:`%s` " % local
            return x

        d = re.sub('#([A-Za-z]*)', fixup_class_refs, d)
        d = re.sub('%([A-Za-z0-9_]*)', fixup_class_refs, d)

        def fixup_param_refs(match):
            return "`%s`" % match.group(1)

        d = re.sub('@([A-Za-z0-9_]*)', fixup_param_refs, d)

        def fixup_function_refs(match):
            x = match.group(1)
            if x in self._types:
                return ":func:`%s`" % self._types[x]
            return x

        d = re.sub('([a-z0-9_]+)\(\)', fixup_function_refs, d)

        d = d.replace("NULL", ":obj:`None`")
        d = d.replace("%NULL", ":obj:`None`")
        d = d.replace("%TRUE", ":obj:`True`")
        d = d.replace("TRUE", ":obj:`True`")
        d = d.replace("%FALSE", ":obj:`False`")
        d = d.replace("FALSE", ":obj:`False`")

        return d

    def parse_class(self, name, obj):
        # bases = ", ".join(map(lambda x: x.__name__, obj.__bases__))
        docs = self._classes.get(name, "")

        return """
class %s(object):
    r'''
%s
    '''\n""" % (name, docs.encode("utf-8"))

    def parse_function(self, name, obj, method=False):
        """Returns python code for the object"""

        doc = str(obj.__doc__)
        first_line = doc and doc.splitlines()[0] or ""
        match = re.match("(.*?)\((.*?)\)( -> )?(.*)", first_line)
        if not match:
            return

        groups = match.groups()
        func_name, args, dummy, ret = groups

        args = args and args.split(",") or []
        args = [a.strip() for a in args]

        ret = ret and ret.split(",") or []

        arg_map = [(a.split(":")[0].strip(), a.split(":")[-1].strip()) for a in args]

        arg_names = [a[0] for a in arg_map]
        if method:
            arg_names.insert(0, "self")
        arg_names = ", ".join(arg_names)

        docs = []
        for key, value in arg_map:
            param_key = name + "." + key
            text = self._fix(self._parameters.get(param_key, ""))
            docs.append(":param %s: %s" % (key, text))
            docs.append(":type %s: :class:`%s`" % (key, value))

        if name in self._returns:
            # don't allow newlines here
            text = self._fix(self._returns[name])
            doc_string = " ".join(text.splitlines())
            docs.append(":returns:")
            docs.append("    %s" % doc_string)
            if ret:
                docs.append("    , %s" % ", ".join(ret))
        elif ret:
            docs.append(":returns:")
            docs.append("    %s" % ", ".join(ret))
        docs.append("")

        if name in self._functions:
            docs.append(self._functions[name])

        docs = "\n".join(docs)

        final = """
def %s(%s):
    r'''
%s
    '''
""" % (func_name, arg_names, docs.encode("utf-8"))

        return final


class MainGenerator(object):

    DEST = "_docs"

    def __init__(self):
        if os.path.exists(self.DEST):
            shutil.rmtree(self.DEST)

        os.mkdir(self.DEST)
        self._subs = []

    def get_generator(self, namespace, name):
        gen = Generator(self.DEST, namespace, name)
        self._subs.append(gen.get_index_name())
        return gen

    def finalize(self):
        with open(os.path.join(self.DEST, "index.rst"), "wb") as h:
            h.write("""\
Python GObject Introspection Documentation
==========================================

.. toctree::
    :maxdepth: 1

""")

            for sub in self._subs:
                h.write("    %s\n" % sub)


        dest_conf = os.path.join(self.DEST, "conf.py")
        build_dir = os.path.join(self.DEST, "_build")
        shutil.copy("conf.py", dest_conf)
        theme_dest = os.path.join(self.DEST, "minimalism")
        shutil.copytree("minimalism", theme_dest)
        subprocess.call(["sphinx-build", self.DEST, build_dir])


class Generator(object):

    def __init__(self, dir_, namespace, version):
        # create the basic package structure
        self.namespace = namespace
        self.version = version
        nick = "%s_%s" % (namespace, version)
        self.index_name = os.path.join(nick, "index")
        self.prefix = os.path.join(dir_, nick)
        os.mkdir(self.prefix)
        module_path = os.path.join(self.prefix, namespace + ".py")
        self.module = open(module_path, "wb")

        func_name = "functions.rst"
        func_path = os.path.join(self.prefix, func_name)
        self.func_handle = open(func_path, "wb")
        self.func_handle.write("""
Functions
=========
""")

        class_name = "classes.rst"
        class_path = os.path.join(self.prefix, class_name)
        self.class_handle = open(class_path, "wb")
        self.class_handle.write("""
Classes
=======
""")

        # utf-8 encoded .py
        self.module.write("# -*- coding: utf-8 -*-\n")

    def get_index_name(self):
        return self.index_name

    def add_function(self, name, code):
        """Add a function"""

        if not isinstance(code, str):
            code = code.encode("utf-8")

        self.module.write(code)
        h = self.func_handle
        h.write(".. autofunction:: %s\n\n" % name)

    def add_class(self, name, code, members=None):
        """Add a class"""

        if not isinstance(code, str):
            code = code.encode("utf-8")

        self.module.write(code)
        if members:
            for m in members:
                m = "\n".join(["    %s" % l for l in m.splitlines()])
                self.module.write(m)

        h = self.class_handle
        h.write("""
.. autoclass:: %s
    :members:
""" % name)

    def add_struct(self, name, code):
        self.add_class(name, code)

    def finalize(self):
        func_name = os.path.basename(self.func_handle.name)
        class_name = os.path.basename(self.class_handle.name)

        with open(os.path.join(self.prefix, "index.rst"),  "wb") as h:
            title = "%s %s" % (self.namespace, self.version)
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

        # make sure the generated code is valid python
        with open(self.module.name, "rb") as h:
            exec h.read() in {}


def create_docs(main_gen, namespace, version):
    gen = main_gen.get_generator(namespace, version)
    mod = import_namespace(namespace, version)
    repo = Repository(namespace, version)

    from gi.repository import GObject
    class_base = GObject.Object
    struct_base = GObject.Value.__mro__[-2]

    for key in dir(mod):
        if key.startswith("_"):
            continue
        obj = getattr(mod, key)

        name = "%s.%s" % (namespace, key)

        if isinstance(obj, types.FunctionType):
            code = repo.parse_function(name, obj)
            if code:
                gen.add_function(name, code)
        elif inspect.isclass(obj):
            if issubclass(obj, class_base):
                funcs = []

                for attr in dir(obj):
                    if attr.startswith("_"):
                        continue

                    func_key = name + "." + attr
                    try:
                        attr_obj = getattr(obj, attr)
                    except NotImplementedError:
                        # FIXME.. pgi exposes methods it can't compile
                        continue
                    if isinstance(attr_obj, types.MethodType):
                        code = repo.parse_function(func_key, attr_obj, method=True)
                        if code:
                            funcs.append(code)

                code = repo.parse_class(key, obj)
                if code:
                    gen.add_class(name, code, members=funcs)
            else:
                code = repo.parse_class(key, obj)
                if code:
                    gen.add_class(name, code)
        else:
            continue

    gen.finalize()


if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print "%s <namespace-version>..." % sys.argv[0]
        raise SystemExit(1)

    gen = MainGenerator()

    for arg in sys.argv[1:]:
        namespace, version = arg.split("-")
        print "Create docs: Namespace=%s, Version=%s" % (namespace, version)
        create_docs(gen, namespace, version)

    gen.finalize()
