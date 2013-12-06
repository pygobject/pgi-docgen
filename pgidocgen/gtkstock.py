# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import re


# Adapted from the PyGObject-Tutorial code
# Copyright by Sebastian Pölsterl
def parse_stock_icon(name):
    """Returns a reST image block for a stock icon.

    e.g. name == 'Gtk.STOCK_ORIENTATION_LANDSCAPE'
    """

    img_p = re.compile("fileref=\"(.+?)\"")
    define_p = re.compile("\\s+")
    mapping = {}

    paths = [
        "/usr/include/gtk-3.0/gtk/deprecated/gtkstock.h",
        "/usr/include/gtk-3.0/gtk/gtkstock.h",
    ]

    for path in paths:
        if os.path.exists(path):
            header_path = path
            break
    else:
        raise LookupError("gtk header files missing: gtkstock.h not found")

    with open(header_path, "rb") as fp:
        imgs = []
        item = None
        for line in fp:
            if "inlinegraphic" in line:
                m = img_p.search(line)
                if m is not None:
                    imgs.append(m.group(1))

            if line.startswith("#define GTK_"):
                item = define_p.split(line)[1].replace("GTK_", "Gtk.")
                mapping[item] = imgs
                imgs = []

    base = "../../stockicons/"
    #base = "http://developer.gnome.org/gtk3/stable/"
    if not name in mapping:
        print "W: no image found for %r" % name
        return ""

    docs = ""
    for fn in mapping[name]:
        title = ""
        if "-ltr" in fn:
            title = "LTR variant:"
        elif "-rtl" in fn:
            title = "RTL variant:"
        docs += """

%s

.. image:: %s
    :alt: %s

""" % (title, base + fn, fn)

    return docs
