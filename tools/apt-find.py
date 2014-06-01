#!/usr/bin/python
# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""Produces a list of packages to install to get all gir/typelibs in Debian"""

import apt


if __name__ == "__main__":
    cache = apt.Cache()
    cache.open(None)

    gir_names = set()
    source_names = set()
    for name in cache.keys():
        if name.startswith("gir1.2-") and ":" not in name:
            package = cache[name]
            for version in package.versions:
                source = version.source_name
                source_names.add(source)
            gir_names.add(name)

    dev_packages = set()
    for name in cache.keys():
        package = cache[name]
        shortname = package.shortname
        for version in package.versions:
            source = version.source_name
            if source in source_names and shortname.endswith("-dev"):
                dev_packages.add(shortname)

    print "sudo aptitude install " + " ".join(dev_packages | gir_names)
