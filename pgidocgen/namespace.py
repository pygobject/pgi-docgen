# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import gc
import ctypes
import re
import shelve
import inspect
import collections
from xml.dom import minidom

from . import util
from .girdata import load_doc_references
from .overrides import parse_override_docs


SHELVE_CACHE = None


def set_cache_prefix_path(path):
    global SHELVE_CACHE

    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    SHELVE_CACHE = path


def get_namespace(namespace, version, _cache={}):

    key = str(namespace + "-" + version)
    protocol = 3

    if key not in _cache:
        if SHELVE_CACHE:
            d = shelve.open(SHELVE_CACHE, protocol=protocol)
            if key in d:
                _cache[key] = d[key]
                d.close()
            else:
                d.close()
                ns = Namespace(namespace, version)
                # make sure we save a fully populated instance
                for k, v in list(type(ns).__dict__.items()):
                    if isinstance(v, util.cached_property):
                        getattr(ns, k)
                d = shelve.open(SHELVE_CACHE, protocol=protocol)
                d[key] = ns
                d.close()
                _cache[key] = ns
        else:
            _cache[key] = Namespace(namespace, version)

    return _cache[key]


def _get_dom(path, _cache={}):
    # caches the last dom
    if path in _cache:
        return _cache[path]
    _cache.clear()
    # reduce peak memory
    gc.collect()
    with open(path, "rb") as h:
        data = h.read()
        data = re.sub(b"(&#x1c;)", b"?", data)
        _cache[path] = minidom.parseString(data)
    return _cache[path]


def fixup_since(text):
    """Split out the 'Since: X.YZ' text from the documentation and returns
    the remaining documentation and the version string or an empty string
    if not version was found.

    This is needed since the gi parser doesn't extract the version info for
    some types like enum values.

    TODO: fix upstream
    """

    added_since = [""]

    def fixup_since(match):
        version = match.group(2)
        # e.g. "3.10."
        version = version.rstrip(".)")
        # e.g. "ATK-2-16"
        version = version.split("-", 1)[-1].replace("-", ".")
        added_since[0] = version
        return ""

    text = re.sub(
        '(^|\\s+)[(@]?Since\\s*\\\\?:?\\s+([^\\s]+)(\\n|$|\\)|\\. )', fixup_since, text)

    return text, added_since[0]


def _fixup_all_added_since(all_docs):
    """Applies fixup_since() to all docs"""

    for type_, type_docs in all_docs.items():
        for k, e in type_docs.items():
            docs = e.docs
            version = e.version
            deprecated_version = e.deprecated_version
            deprecated = e.deprecated
            changed = False

            if not version:
                docs, version = fixup_since(docs)
                changed = True

            if not deprecated_version:
                deprecated, deprecated_version = fixup_since(deprecated)
                changed = True

            if changed:
                type_docs[k] = DocEntry(docs, version,
                                        deprecated_version, deprecated)


def get_versions(all_docs):
    """Collects all 'added since' and 'deprecated since' versions"""

    versions = set()
    for type_, type_docs in all_docs.items():
        for k, e in type_docs.items():
            if e.version:
                versions.add(e.version)
            if e.deprecated_version:
                versions.add(e.deprecated_version)
    return versions


DocEntry = collections.namedtuple(
    "DocEntry", ["docs", "version", "deprecated_version", "deprecated"])


class Namespace(object):

    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

        self._types = None
        self._type_structs = None
        self._shadow_map = None
        self._iparams = None

    def _ensure_types(self):
        if self._types is not None:
            return
        dom = _get_dom(self.path)
        self._types, self._type_structs, self._shadow_map, self._iparams = \
            _parse_types(dom, self.import_module(), self.namespace)

    @util.cached_property
    def shared_libraries(self):
        dom = _get_dom(self.path)
        namespace_elm = dom.getElementsByTagName("namespace")[0]
        shared_library = namespace_elm.getAttribute("shared-library")
        return shared_library.split(",") if shared_library else []

    @util.cached_property
    def shadow_map(self):
        self._ensure_types()
        return self._shadow_map

    @util.cached_property
    def doc_references(self):
        return load_doc_references(self.namespace, self.version)

    def import_module(self):
        """Imports the module and initializes all dependencies.

        Can raise ImportError.
        """

        # This is all needed because some modules depending on GStreamer
        # segfaults if Gst.init() isn't called before introspecting them
        to_load = list(reversed(self.all_dependencies))
        to_load += [(self.namespace, self.version)]

        for (namespace, version) in to_load:
            module = util.import_namespace(namespace, version)

        return module

    @util.cached_property
    def private(self):
        return _parse_private(_get_dom(self.path), self.namespace)

    @util.cached_property
    def override_docs(self):
        return parse_override_docs(self.namespace, self.version)

    @util.cached_property
    def docs(self):
        docs = _parse_docs(_get_dom(self.path))
        _fixup_all_added_since(docs)
        return docs

    @util.cached_property
    def types(self):
        self._ensure_types()
        return self._types

    @util.cached_property
    def type_structs(self):
        """A mapping of C type struct IDs to Python type IDs.

        e.g. GObjectClass -> GObject.Object
        """

        self._ensure_types()
        return self._type_structs

    @util.cached_property
    def instance_params(self):

        self._ensure_types()
        return self._iparams

    @util.cached_property
    def path(self):
        """The absolute path to the gir file.

        e.g. "/usr/share/gir-1.0/GObject-2.0.gir"
        """

        key = "%s-%s" % (self.namespace, self.version)
        return util.get_gir_files()[key]

    @util.cached_property
    def dependencies(self):
        """A list of (namespace, version) tuples for all direct dependencies
        of this namespace.
        """

        dom = _get_dom(self.path)

        # dependencies
        deps = []
        for include in dom.getElementsByTagName("include"):
            name = include.getAttribute("name")
            version = include.getAttribute("version")
            deps.append((name, version))

        # these are not always included, but we need them
        # for base types
        if not deps:
            if self.namespace not in ("GObject", "GLib"):
                deps.append(("GObject", "2.0"))

        return deps

    @util.cached_property
    def all_dependencies(self):
        """A list of (namespace, version) tuples for all transitive
        dependencies of this namespace.
        """

        loaded = []
        to_load = list(self.dependencies)
        while to_load:
            key = to_load.pop()
            if key in loaded:
                continue
            sub_ns = get_namespace(*key)
            loaded.append(key)
            to_load.extend(sub_ns.dependencies)

        return loaded

    def __repr__(self):
        return "%s(%s, %s)" % (
            type(self).__name__, self.namespace, self.version)


def get_cairo_types():
    """Creates an (incomplete) c symbol to python key mapping for
    pycairo/cairocffi
    """

    try:
        import cairo
    except ImportError:
        import cairocffi as cairo

    lib = ctypes.CDLL("libcairo.so.2")

    def get_mapping(obj, prefix):
        map_ = {}
        for arg in dir(obj):
            if arg.startswith("_"):
                continue
            c_name = "_".join(filter(None, ["cairo", prefix, arg]))
            if hasattr(lib, c_name):
                map_[c_name] = ["cairo." + obj.__name__ + "." + arg]
        type_name = "_".join(filter(None, ["cairo", prefix, "t"]))
        map_[type_name] = ["cairo." + obj.__name__]
        return map_

    types = {}
    types.update(get_mapping(cairo.Context, ""))
    types.update(get_mapping(cairo.Surface, "surface"))
    types.update(get_mapping(cairo.Pattern, "pattern"))
    types.update(get_mapping(cairo.Matrix, "matrix"))
    types.update(get_mapping(cairo.FontFace, "font_face"))

    return types


def get_base_types():
    return {
        "NULL": ["None"],
        "TRUE": ["True"],
        "FALSE": ["False"],
        "gint": ["int"],
        "gboolean": ["bool"],
        "gchar": ["str"],
        "gdouble": ["float"],
        "glong": ["int"],
        "gfloat": ["float"],
        "guint": ["int"],
        "gulong": ["int"],
        "char": ["str"],
        "gpointer": ["object"],
    }


def _parse_types(dom, module, namespace):
    """Create a mapping of various C names to python names"""

    type_structs = {}
    types = collections.defaultdict(set)
    shadow_map = {}
    instance_params = {}

    def add(c_name, py_name):
        assert py_name.count(".") and c_name, (c_name, py_name)
        # escape each potential attribute
        py_name = ".".join(
            map(util.escape_parameter, py_name.split(".")))
        types[c_name].add(py_name)
        return py_name

    # key is the shadowed function name (gir name)
    all_shadows = {}
    all_shadowed_by = {}

    # c symbols we want to skip, but we need them for shadowed func, so remove
    # them later
    skipped = set()

    # gtk_main -> Gtk.main
    # gtk_dialog_get_response_for_widget ->
    #     Gtk.Dialog.get_response_for_widget
    elements = dom.getElementsByTagName("function")
    elements += dom.getElementsByTagName("constructor")
    elements += dom.getElementsByTagName("method")
    for t in elements:
        shadows = t.getAttribute("shadows")
        shadowed_by = t.getAttribute("shadowed-by")
        introspectable = bool(int(t.getAttribute("introspectable") or "1"))
        local_name = t.getAttribute("name")
        c_name = t.getAttribute("c:identifier")
        assert c_name

        ip = t.getElementsByTagName("instance-parameter")
        instance_param = ip[0].getAttribute("name") if ip else ""

        # Copy escaping from gi: Foo.break -> Foo.break_
        full_name = local_name
        parent = t.parentNode

        # glib:boxed toplevel in Farstream-0.1
        if not parent.getAttribute("name"):
            continue

        while parent.getAttribute("name"):
            full_name = parent.getAttribute("name") + "." + full_name
            parent = parent.parentNode

        if shadows:
            parent_name = full_name.rsplit(".", 1)[0]
            all_shadows[parent_name + "." + shadows] = c_name
        if shadowed_by:
            # in case something shadows itself just ignore it
            if shadowed_by != local_name:
                all_shadowed_by[full_name] = c_name

        if not introspectable or shadowed_by:
            skipped.add(c_name)

        set_name = add(c_name, full_name)
        if instance_param:
            # TODO: shadowed..?
            instance_params[set_name] = instance_param

    for key, value in all_shadows.items():
        shadow_map[all_shadowed_by.pop(key)] = value
    assert not all_shadowed_by, all_shadowed_by
    del all_shadowed_by
    del all_shadows

    # enums etc. GTK_SOME_FLAG_FOO -> Gtk.SomeFlag.FOO
    for t in dom.getElementsByTagName("member"):
        c_name = t.getAttribute("c:identifier")
        assert c_name
        # only match constants
        if c_name != c_name.upper() or "_" not in c_name:
            continue
        class_name = t.parentNode.getAttribute("name")
        field_name = t.getAttribute("name").upper()
        local_name = namespace + "." + class_name + "." + field_name
        add(c_name, local_name)

    # classes
    elements = dom.getElementsByTagName("class")
    elements += dom.getElementsByTagName("interface")
    elements += dom.getElementsByTagName("enumeration")
    elements += dom.getElementsByTagName("bitfield")
    elements += dom.getElementsByTagName("callback")
    elements += dom.getElementsByTagName("union")
    for t in elements:
        # only top level
        if t.parentNode.tagName != "namespace":
            continue

        c_name = t.getAttribute("c:type")
        c_name = c_name or t.getAttribute("glib:type-name")
        introspectable = bool(int(t.getAttribute("introspectable") or "1"))

        # e.g. GObject _Value__data__union
        if not c_name:
            continue

        if not introspectable:
            skipped.add(c_name)
            continue

        type_name = t.getAttribute("name")
        add(c_name, namespace + "." + type_name)

    # cairo_t -> cairo.Context
    for t in dom.getElementsByTagName("record"):
        c_name = t.getAttribute("c:type")
        # Gee-0.8 HazardPointer
        if not c_name:
            continue

        introspectable = bool(int(t.getAttribute("introspectable") or "1"))
        if not introspectable:
            skipped.add(c_name)
            continue

        type_for = t.getAttribute("glib:is-gtype-struct-for")
        if type_for:
            type_structs[c_name] = namespace + "." + type_for

        type_name = t.getAttribute("name")
        if type_name.startswith("_"):
            continue
        add(c_name, namespace + "." + type_name)

    # G_TIME_SPAN_MINUTE -> GLib.TIME_SPAN_MINUTE
    for t in dom.getElementsByTagName("constant"):
        c_name = t.getAttribute("c:type")
        c_name = c_name or t.getAttribute("c:identifier")
        if t.parentNode.tagName == "namespace" and c_name:
            name = namespace + "." + t.getAttribute("name")
            add(c_name, name)

    # make c defs which are replaced point to the key of the replacement
    # so that: "gdk_threads_add_timeout_full" -> Gdk.threads_add_timeout
    for shadowed, shadowing in shadow_map.items():
        types[shadowing] = set(types[shadowed])
        types[shadowed].clear()

    # We wont have a Python function for these, so don't expose them
    for c_name in skipped:

        def is_available(mod, name):
            path, final = name.rsplit(".", 1)
            m = mod
            for attr in path.split(".")[1:]:
                try:
                    m = getattr(m, attr)
                except AttributeError:
                    return False
            if not inspect.isclass(m):
                return hasattr(m, final)
            try:
                return util.is_attribute_owner(m, final)
            except AttributeError:
                return False

        # shadowed get cleared above so this should be non-introspectable.
        # but overrides might make them available using other API, so check
        # for that before deciding that it isn't available to Python
        types[c_name] = set(
            filter(lambda n: is_available(module, n), types[c_name]))

    if namespace == "GObject":
        # these come from overrides and aren't in the gir
        # e.g. G_TYPE_INT -> GObject.TYPE_INT
        from gi.repository import GObject

        for key in dir(GObject):
            if key.startswith("TYPE_"):
                types["G_" + key].add("GObject." + key)
            elif key.startswith(("G_MAX", "G_MIN")):
                types[key].add("GObject." + key)

        types["GBoxed"] = set(["GObject.GBoxed"])
        types["GType"] = set(["GObject.GType"])
    elif namespace == "GLib":
        from gi.repository import GLib

        types.update(get_base_types())

        for k in dir(GLib):
            if re.match("MINU?INT\\d+", k) or re.match("MAXU?INT\\d+", k):
                types["G_" + k].add("GLib." + k)

        # there is a weird type called "s" in VariantBuilder
        types.pop("s", None)

    elif namespace == "cairo":
        types.update(get_cairo_types())

    # convert sets to lists and sort them so the best is first
    # (prefer methods over functions)
    types = dict(types)
    for key, values in types.items():
        values = sorted(values, key=lambda v: -v.count("."))
        types[key] = values

    return types, type_structs, shadow_map, instance_params


def _parse_private(dom, namespace):
    private = set()

    def is_empty(node):
        for child in record.childNodes:
            if child.nodeType == child.TEXT_NODE:
                continue
            if child.tagName == "source-position":
                continue
            return False
        return True

    # if disguised and no record content... not perfect, but
    # we have no other way
    for record in dom.getElementsByTagName("record"):
        is_gtype_struct = bool(record.getAttribute("glib:is-gtype-struct-for"))
        is_private = record.getAttribute("name").endswith("Private")
        if is_private and not is_gtype_struct and is_empty(record):
            name = namespace + "." + record.getAttribute("name")
            private.add(name)

    return private


def _parse_docs(dom):
    """Parse docs"""

    all_ = {}
    all_shadowed = {}
    parameters = {}
    sparas = {}
    returns = {}
    sreturns = {}
    signals = {}
    properties = {}
    fields = {}

    all_docs = {
        "all": all_,
        "all_shadowed": all_shadowed,
        "parameters": parameters,
        "signal-parameters": sparas,
        "returns": returns,
        "signal-returns": sreturns,
        "signals": signals,
        "properties": properties,
        "fields": fields,
    }

    tag_names = [
        [("glib:signal",), signals],
        [("field",), fields],
        [("property",), properties],
        [("parameter", "glib:signal"), sparas],
        [("parameter", "function-macro"), parameters],
        [("parameter", "function"), parameters],
        [("parameter", "method"), parameters],
        [("parameter", "callback"), parameters],
        [("parameter", "constructor"), parameters],
        [("parameter", "function-inline"), parameters],
        [("parameter", "method-inline"), parameters],
        [("instance-parameter", "method"), parameters],
        [("instance-parameter", "method-inline"), parameters],
        [("instance-parameter", "function"), parameters],
        [("return-value", "callback"), returns],
        [("return-value", "method"), returns],
        [("return-value", "function"), returns],
        [("return-value", "constructor"), returns],
        [("return-value", "function-inline"), returns],
        [("return-value", "method-inline"), returns],
        [("return-value", "glib:signal"), sreturns],
        [("interface",), all_],
        [("method",), all_],
        [("function",), all_],
        [("constant",), all_],
        [("record",), all_],
        [("enumeration",), all_],
        [("member",), all_],
        [("callback",), all_],
        [("alias",), all_],
        [("constructor",), all_],
        [("class",), all_],
        [("bitfield",), all_],
        # vfuncs last, since they replace normal onces in case of name clashes
        [("virtual-method",), all_],
        [("parameter", "virtual-method"), parameters],
        [("instance-parameter", "virtual-method"), parameters],
        [("return-value", "virtual-method"), returns],
    ]

    def get_child_by_tag(node, tag_name):
        for sub in node.childNodes:
            try:
                if sub.tagName == tag_name:
                    return sub
            except AttributeError:
                continue

    path_seen = set()
    path_done = set()

    all_elements = dom.getElementsByTagName("*")

    def get_elements(name):
        for elm in all_elements:
            if elm.tagName == name:
                yield elm

    for target, result in tag_names:
        tag = target[0]
        needed = target[1:]

        for e in get_elements(tag):
            doc_elm = get_child_by_tag(e, "doc")
            docs = (doc_elm and doc_elm.firstChild.nodeValue) or ""
            version = e.getAttribute("version")

            # old gir had the deprecation text in the attribute, new
            # gir in the <doc-deprecated> tag
            deprecated = e.getAttribute("deprecated")
            if deprecated in "01":
                deprecated = ""

            dep_elm = get_child_by_tag(e, "doc-deprecated")
            dep_elm_string = (dep_elm and dep_elm.firstChild.nodeValue) or ""
            deprecated = dep_elm_string or deprecated

            deprecated_version = e.getAttribute("deprecated-version")

            def get_name(elm):
                """Returns a string (maybe be empty) or None"""

                # if this entry shadows another one use its name
                shadows = elm.getAttribute("shadows")
                if shadows:
                    n = shadows
                else:
                    if elm.hasAttribute("name"):
                        n = elm.getAttribute("name")
                    elif elm.hasAttribute("glib:name"):
                        n = elm.getAttribute("glib:name")
                    else:
                        return

                if elm.tagName == "virtual-method":
                    # pgi/pygobject escape before prefixing
                    n = "do_" + util.escape_identifier(n)
                elif elm.tagName == "member":
                    # enum/flag values
                    n = n.upper()

                return n

            # these can be nested, so if there is not name, don't go up the tree
            # or we might up ending up with the same name as the parent record
            requires_name = ["record"]

            l = []
            tags = []
            current = e
            name = get_name(current)
            if name is not None:
                l.append(name)
            elif current.tagName in requires_name:
                continue
            shadowed = False
            while current.tagName != "namespace":
                # this gets shadowed by another entry, bail out
                if current.getAttribute("shadowed-by"):
                    shadowed = True
                tags.append(current.tagName)
                current = current.parentNode
                # Tracker-0.16 includes <constant> outside of <namespace>
                if current.tagName == "repository":
                    break
                name = get_name(current)
                if name is not None:
                    l.insert(0, name)

            # for shadowed function docs we save docs anyway since we
            # can include them in the function docs for the replacement.
            # This can be helpful since some replacements just reference
            # the shadowed function, which we don't include.
            if result is all_shadowed:
                result = all_
            if shadowed:
                if result is all_:
                    result = all_shadowed
                else:
                    continue

            path_seen.add(tuple(tags))

            if any(a for a in needed if a not in tags):
                continue

            path_done.add(tuple(tags))

            key = ".".join(map(util.escape_parameter, l))

            if tag in ("method", "constructor"):
                assert len(l) > 2

            new = DocEntry(docs, version, deprecated_version, deprecated)
            # Atspi-2.0 has some things declared twice, so
            # don't be too strict here.

            # We prefix vfuncs with "do_", but this could still clash here
            if "virtual-method" not in target:
                assert key not in result or new == result[key], key
            result[key] = new

    assert not (path_seen - path_done), path_seen - path_done

    return all_docs
