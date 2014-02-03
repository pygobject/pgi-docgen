#!/usr/bin/python
# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os


LIBS = {
    "https://git.gnome.org/browse/gtk+/plain/gtk+.doap":
        ["Gtk-3.0"],
    "http://cgit.freedesktop.org/gstreamer/gstreamer/plain/gstreamer.doap":
        ["Gst-1.0", "GstBase-1.0", "GstCheck-1.0", "GstController-1.0"],
    "http://cgit.freedesktop.org/gstreamer/gst-plugins-base/plain/gst-plugins-base.doap":
        ["GstAllocators-1.0", "GstApp-1.0", "GstAudio-1.0", "GstFft-1.0"],
    "https://git.gnome.org/browse/glib/plain/glib.doap":
        ["GLib-2.0", "GObject-2.0", "Gio-2.0"],
    "https://git.gnome.org/browse/atk/plain/atk.doap":
        ["Atk-1.0"],
    "https://git.gnome.org/browse/cogl/plain/cogl.doap":
        ["Cogl-1.0", "CoglPango-1.0"],
}


if __name__ == "__main__":
    import requests

    for url, ns_list in LIBS.items():
        print url
        r = requests.get(url)
        for ns in ns_list:
            with open(os.path.join("doap", ns), "wb") as h:
                h.write(r.content)
