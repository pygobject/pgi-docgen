#!/usr/bin/python
# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
Takes multiple sphinx search index files in subdirectories and
merges them into one, adjusting the paths in the final index accordingly
"""

import os
import sys

from sphinx.search import js_index


class SearchIndexMerger(object):

    def __init__(self):
        self._indices = {}
        self._modules = []

    def add_index(self, namespace, index):
        if index is not None:
            self._indices[namespace] = index
        self._modules.append(namespace)

    def merge(self):

        if not self._indices:
            raise ValueError

        done = {}

        # not sphinx..
        done["modules"] = sorted(self._modules)

        # ENVVERSION (const)
        first = self._indices[self._indices.keys()[0]]
        done["envversion"] = first["envversion"]

        # FILENAMES/TITLES (list)
        def prefix_fn(ns, fn):
            return ns + "/" + fn

        new_titles = []
        new_filenames = []
        for ns, index in self._indices.iteritems():
            for fn, title in zip(index["filenames"], index["titles"]):
                new_filenames.append(prefix_fn(ns, fn))
                # add the namespace to title not containing the module name
                if "." not in title:
                    title = "%s - %s" % (ns.replace("-", " "), title)
                new_titles.append(title)
        done["filenames"] = new_filenames
        done["titles"] = new_titles

        fn_index_lookup = dict((fn, i) for i, fn in enumerate(new_filenames))

        def get_fn_index(ns, old_index):
            value = self._indices[ns]["filenames"][old_index]
            value = prefix_fn(ns, value)
            return fn_index_lookup[value]

        def merge_term_mapping(key):
            new_terms = {}
            for ns, index in self._indices.iteritems():
                for k, old_refs in index[key].iteritems():
                    if not isinstance(old_refs, list):
                        old_refs = [old_refs]
                    if k not in new_terms:
                        new_terms[k] = []
                    new_refs = new_terms[k]
                    for ref in old_refs:
                        new_refs.append(get_fn_index(ns, ref))

            for k, v in new_terms.iteritems():
                # remove lists again for only one entry
                if len(v) == 1:
                    new_terms[k] = v[0]

            return new_terms

        # TERMS (word -> fn index list, or one index)
        done["terms"] = merge_term_mapping("terms")

        # TITLETERMS: (word -> fn index list)
        done["titleterms"] = merge_term_mapping("titleterms")

        pairs = []
        for ns, index in self._indices.iteritems():
            for k, v in index["objnames"].items():
                pair = (index["objtypes"][k], v)
                if pair not in pairs:
                    pairs.append(pair)

        # OBJNAMES/OBJTYPES
        new_objnames = {}
        new_objtypes = {}

        for i, (type_, name) in enumerate(pairs):
            new_objnames[str(i)] = name
            new_objtypes[str(i)] = type_

        done["objnames"] = new_objnames
        done["objtypes"] = new_objtypes

        def get_obj_index(ns, old_index):
            old_index = str(old_index)
            index = self._indices[ns]
            value = index["objtypes"][old_index]
            for k, v in done["objtypes"].items():
                if value == v:
                    return int(k)
            assert 0

        # OBJECTS
        new_objects = {}
        for ns, index in self._indices.iteritems():
            for k, attributes in index["objects"].iteritems():
                if k not in new_objects:
                    new_objects[k] = {}
                new_attributes = new_objects[k]

                for attr, v in attributes.items():
                    fn_index, objtype_index, prio, shortanchor = v
                    fn_index = get_fn_index(ns, fn_index)
                    objtype_index = get_obj_index(ns, objtype_index)
                    new_v = [fn_index, objtype_index, prio, shortanchor]
                    # FIXME: there are clashes, last thing wins for now
                    # .. because of multiple versions
                    new_attributes[attr] = new_v

        done["objects"] = new_objects

        assert (set(first.keys()) ^ set(done.keys())) == set(["modules"])

        return done


def fixup_props_signals(index):
    """Move things around so that signals and properties
    better match devhelp output.
    """

    objects = index["objects"]

    if "" not in objects:
        objects[""] = {}

    sig_index = len(index["objnames"]) + 1
    index["objnames"][str(sig_index)] = ["gobject", "signal", "GObject Signal"]
    index["objtypes"][str(sig_index)] = "gobject:signal"

    prop_index = len(index["objnames"]) + 1
    index["objnames"][str(prop_index)] = [
        "gobject", "property", "GObject Property"]
    index["objtypes"][str(prop_index)] = "gobject:property"

    for attr_key, attributes in objects.items():
        if attr_key.endswith(".props"):
            ns = attr_key.rsplit(".", 1)[0]
            for k, v in attributes.iteritems():
                v[1] = prop_index
                v[3] = attr_key + "." + k
                k = "%s (%s)" % (k.replace("_", "-"), ns)
                objects[""][k] = v
            del objects[attr_key]
        elif attr_key.endswith(".signals"):
            ns = attr_key.rsplit(".", 1)[0]
            for k, v in attributes.iteritems():
                v[1] = sig_index
                v[3] = attr_key + "." + k
                k = "%s (%s)" % (k.replace("_", "-"), ns)
                objects[""][k] = v
            del objects[attr_key]


def merge(path, include_terms=False, exclude_old=True):
    """Merge searchindex files in subdirectories of `path` and
    create a searchindex files under `path`
    """

    groups = {}

    merger = SearchIndexMerger()
    for entry in os.listdir(path):
        index_path = os.path.join(path, entry, "searchindex.js")
        if not os.path.exists(index_path):
            continue

        namespace, version = os.path.basename(
            os.path.dirname(index_path)).split("-")
        with open(index_path, "rb") as h:
            data = h.read()
            mod = js_index.loads(data)
            groups.setdefault(namespace, []).append((version, mod))

    def sort_version_key(version):
        return tuple(map(int, version.split(".")))

    for namespace, entries in sorted(groups.items()):
        # newest first, for name clashes
        entries.sort(key=lambda x: sort_version_key(x[0]), reverse=True)
        if exclude_old:
            entries

        for i, (version, mod) in enumerate(entries):
            key = namespace + "-" + version
            if exclude_old and i > 0:
                merger.add_index(key, None)
                continue
            fixup_props_signals(mod)
            if not include_terms:
                mod["terms"].clear()
                mod["titleterms"].clear()
            merger.add_index(key, mod)

    with open(os.path.join(path, "searchindex.js"), "wb") as h:
        output = merger.merge()
        h.write(js_index.dumps(output))
