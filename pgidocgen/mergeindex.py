#!/usr/bin/env python
# Copyright 2014,2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
Takes multiple sphinx search index files in subdirectories and
creates a new custom search index (with a different structure) containing
all symbols.
"""

import os
import io

from sphinx.search import js_index

from .util import unescape_parameter

from typing import TypedDict


class IndexObject(TypedDict):
    objnames: dict[str, list[str]]
    objtypes: dict[str, str]
    docnames: list[str]
    filenames: list[str]
    titles: list[str]
    objects: dict[str, list[list[int | str]]]


class PartialIndexObject(IndexObject, total=False):
    objnames: dict[str, list[str]]
    objtypes: dict[str, str]
    docnames: list[str]
    filenames: list[str]
    titles: list[str]
    objects: dict[str, list[list[int | str]]]


class DoneIndexObject(PartialIndexObject, total=False):
    namespaces: dict[str, PartialIndexObject]


class SearchIndexMerger(object):

    def __init__(self):
        self._indices: dict[str, IndexObject] = {}

    def add_index(self, namespace: str, index: IndexObject):
        if index is not None:
            assert namespace not in self._indices
            self._indices[namespace] = index

    def load_index(self, namespace: str, index_path: str):
        with io.open(index_path, "r", encoding="utf-8") as h:
            data = h.read()
            mod = js_index.loads(data)
            self.add_index(namespace, mod)

    def merge(self) -> DoneIndexObject:

        if not self._indices:
            raise ValueError

        done: DoneIndexObject = {
            # Initialise empty vars to satisfy type checker
            "objtypes": {},
            "namespaces": {}
        }
        namespaces: dict[str, PartialIndexObject] = {}

        pairs: list[tuple[str, list[str]]] = []
        for ns, index in self._indices.items():
            for k, v in index["objnames"].items():
                pair = (index["objtypes"][k], v)
                if pair not in pairs:
                    pairs.append(pair)

        pairs.append(
            ("gobject:vfunc", ["gobject", "vfunc", "Virtual Function"]))
        pairs.append(
            ("gobject:signal", ["gobject", "signal", "GObject Signal"]))
        pairs.append(
            ("gobject:property", ["gobject", "property", "GObject Property"]))

        # OBJNAMES/OBJTYPES
        new_objnames = {}
        new_objtypes = {}

        objtype_indices = {
            "gobject:property": 0
        }
        for i, (type_, name) in enumerate(pairs):
            new_objnames[str(i)] = name
            new_objtypes[str(i)] = type_
            objtype_indices[type_] = i

        done["objnames"] = new_objnames
        done["objtypes"] = new_objtypes

        def get_obj_index(ns: str, old_index: int | str) -> int:
            inner_old_index = str(old_index)
            index = self._indices[ns]
            value = index["objtypes"][inner_old_index]
            for k, v in done["objtypes"].items():
                if value == v:
                    return int(k)
            assert 0
            return 0

        # OBJECTS
        for ns, index in self._indices.items():
            namespaces[ns] = {}

            new_titles: list[str] = []
            new_filenames: list[str] = []
            new_docnames: list[str] = []
            for docname, fn, title in zip(index["docnames"],
                                          index["filenames"], index["titles"]):
                new_filenames.append(fn)
                new_docnames.append(docname)
                # add the namespace to title not containing the module name
                if "." not in title:
                    title = "%s - %s" % (ns.replace("-", " "), title)
                new_titles.append(title)
            namespaces[ns]["titles"] = new_titles
            namespaces[ns]["filenames"] = new_filenames
            namespaces[ns]["docnames"] = new_docnames

            new_objects: dict[str, list[list[int | str]]] = {}
            for k, attributes in index["objects"].items():
                if "." in k:
                    k = k.split(".", 1)[-1]
                else:
                    k = ""

                orig_k = k
                is_props = False
                is_signals = False
                if k.endswith(".props"):
                    k = ""
                    is_props = True
                elif k.endswith(".signals"):
                    k = ""
                    is_signals = True

                if k not in new_objects:
                    new_objects[k] = []
                new_attributes = new_objects[k]

                for v in attributes:
                    fn_index, objtype_index, prio, _, shortanchor = v
                    attr: str = str(shortanchor)
                    objtype_index = get_obj_index(ns, objtype_index)
                    new_v = [fn_index, objtype_index, prio, shortanchor]

                    # Move things around so that signals and properties
                    # better match devhelp output.
                    if is_props:
                        new_v[1] = objtype_indices["gobject:property"]
                        new_v[3] = orig_k + "." + attr
                        attr = "%s:%s" % (
                            orig_k.rsplit(".", 1)[0], unescape_parameter(attr))
                    elif is_signals:
                        new_v[1] = objtype_indices["gobject:signal"]
                        new_v[3] = orig_k + "." + attr
                        attr = "%s::%s" % (
                            orig_k.rsplit(".", 1)[0], unescape_parameter(attr))
                    elif attr.startswith("do_"):
                        # change vfunc object type
                        # XXX: there could be methods called "do_XXX"..
                        new_v[1] = objtype_indices["gobject:vfunc"]

                    assert attr not in new_attributes
                    new_attributes.append([])

            namespaces[ns]["objects"] = new_objects

        done["namespaces"] = namespaces

        return done


def mergeindex(path: str):
    """Merge searchindex files in subdirectories of `path` and
    create a searchindex files under `path`
    """

    merger = SearchIndexMerger()
    for entry in os.listdir(path):
        index_path = os.path.join(path, entry, "searchindex.js")
        if not os.path.exists(index_path):
            continue

        key = os.path.basename(os.path.dirname(index_path))
        merger.load_index(key, index_path)

    with io.open(os.path.join(path, "searchindex.js"), "w", encoding="utf-8") as h:
        output = merger.merge()
        h.write(js_index.dumps(output))
