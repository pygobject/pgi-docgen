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

    def add_index(self, namespace, index):
        self._indices[namespace] = index

    def merge(self):

        if not self._indices:
            raise ValueError

        done = {}

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
                    new_attributes[attr] = new_v

        done["objects"] = new_objects

        assert not (set(first.keys()) ^ set(done.keys()))

        return done


def merge(path, include_terms=True):
    """Merge searchindex files in subdirectories of `path` and
    create a searchindex files under `path`
    """

    merger = SearchIndexMerger()
    for entry in os.listdir(path):
        index_path = os.path.join(path, entry, "searchindex.js")
        if not os.path.exists(index_path):
            continue

        namespace = os.path.basename(os.path.dirname(index_path))
        with open(index_path, "rb") as h:
            data = h.read()
            mod = js_index.loads(data)
            merger.add_index(namespace, mod)
    
    with open(os.path.join(path, "searchindex.js"), "wb") as h:
        output = merger.merge()
        if not include_terms:
            del output["terms"]
            del output["titleterms"]
        h.write(js_index.dumps(output))
