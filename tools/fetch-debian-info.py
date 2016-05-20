#!/usr/bin/python
# Copyright 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import json
import apt
import subprocess

from pgidocgen.util import shell
from pgidocgen.debian import _extract_control_field, get_repo_typelibs
from pgidocgen.girdata import get_debian_path


if __name__ == "__main__":
    cache = apt.Cache()
    cache.open(None)
    homepages = _extract_control_field("Homepage")

    typelibs = get_repo_typelibs()

    def fixup_desc(t):
        new = []
        for line in t.splitlines():
            if line.startswith(
                    ("This package includes", "This package contains",
                     "This package provides")):
                continue
            new.append(line)
        return "\n".join(new).strip()

    def fixup_summary(t):
        return t.rsplit(" - ", 1)[0].rsplit(" -- ", 1)[0]

    final = {}
    for package, namespaces in typelibs.iteritems():
        candidate = cache[package].candidate
        if not candidate:
            continue

        # For a package containing the typelib search for a direct dependency
        # which is a library and has the same source package.
        # This library package usually has a better description/summary.
        dep_packages = []
        for deps in candidate.get_dependencies("Depends"):
            for dep in deps:
                if dep.name in cache:
                    cand = cache[dep.name].candidate
                    if cand:
                        dep_packages.append(cand)

        for dep in dep_packages:
            if dep.section != "libs":
                continue
            if dep.source_name == candidate.source_name:
                candidate = dep
                break

        homepage = candidate.homepage
        summary = fixup_summary(candidate.summary)
        description = fixup_desc(candidate.description)

        for ns in namespaces:
            final[ns] = {
                "lib": candidate.source_name,
                "homepage": homepage,
                "summary": summary,
                "description": description,
                "debian_package": package,
            }

    cache.close()

    with open(get_debian_path(), "wb") as h:
        h.write(json.dumps(final, sort_keys=True, indent=4))
