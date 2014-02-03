#!/usr/bin/python
# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os


LIBS = {
    "https://git.gnome.org/browse/gtk+/plain/gtk+.doap": ["Gtk-3.0"],
    "http://cgit.freedesktop.org/gstreamer/gstreamer/plain/gstreamer.doap": ["Gst-1.0"],
    "https://git.gnome.org/browse/glib/plain/glib.doap": ["GLib-2.0", "GObject-2.0", "Gio-2.0"]
}


if __name__ == "__main__":
    import requests

    for url, ns_list in LIBS.items():
        print url
        r = requests.get(url)
        for ns in ns_list:
            with open(os.path.join("doap", ns), "wb") as h:
                h.write(r.content)
