# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


class Docs(object):
    """An online accessible instance of gtk-doc.

    (should we add some way to allow multiple versions instead of pointing to
    the latest?)
    """

    def __init__(self, url, doc_id, namespaces):
        self.url = url
        self.doc_id = doc_id
        self.namespaces = namespaces

    @property
    def devhelp_url(self):
        return "%s%s.devhelp2" % (self.url, self.doc_id)

    def __repr__(self):
        return "<%s url=%r doc_id=%r namespaces=%r>" % (
            type(self).__name__, self.url, self.doc_id, self.namespaces)


GTK_DOCS = [
    Docs("https://developer.gnome.org/glib/stable/", "glib", ["GLib-2.0"]),
    Docs("https://developer.gnome.org/gio/stable/", "gio", ["Gio-2.0"]),
    Docs("https://developer.gnome.org/gobject/stable/", "gobject", ["GObject-2.0"]),
    Docs("https://developer.gnome.org/pango/stable/", "pango", ["Pango-1.0"]),
    Docs("https://developer.gnome.org/gdk-pixbuf/unstable/", "gdk-pixbuf", ["GdkPixbuf-2.0"]),
    Docs("https://developer.gnome.org/gdk3/stable/", "gdk3", ["Gdk-3.0"]),
    Docs("https://developer.gnome.org/gtk3/stable/", "gtk3", ["Gtk-3.0"]),
    Docs("http://webkitgtk.org/reference/webkit2gtk/stable/", "webkit2gtk-4.0", ["WebKit2-4.0"]),
    Docs("https://developer.gnome.org/cairo/stable/", "cairo", ["cairo-1.0"]),
    Docs("https://developer.gnome.org/clutter/stable/", "clutter", ["Clutter-1.0"]),
    Docs("http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/", "gstreamer-1.0", ["Gst-1.0"]),
]


def get_generic_library_version(mod):
    """Tries to return a version string of the library version used to create
    the gir or if not available the version of the library dlopened.

    If no version could be found, returns an empty string.
    """

    suffix = ""
    modname = mod.__name__
    for i, (o, l) in enumerate(reversed(zip(modname, modname.lower()))):
        if o != l:
            suffix = modname[-i - 1:].upper()
            break

    const_version = []
    for name in ["MAJOR", "MINOR", "MICRO", "NANO"]:
        for variant in ["VERSION_" + name, name + "_VERSION",
                        suffix + "_" + name, suffix + "_" + name + "_VERSION",
                        suffix + "_VERSION_" + name]:
            if hasattr(mod, variant):
                value = int(getattr(mod, variant))
                const_version.append(value)

    if const_version:
        return ".".join(map(str, const_version))

    func_version = ""
    for name in ["get_version", "version", "util_get_version",
                 "util_get_version_string", "get_version_string",
                 "version_string"]:
        if hasattr(mod, name):
            try:
                value = getattr(mod, name)()
            except TypeError:
                continue

            if isinstance(value, (tuple, list)):
                func_version = ".".join(map(str, value))
                break
            elif isinstance(value, str):
                func_version = value

    return func_version


def get_library_version(mod):
    """Returns a library version as string for a given Python module. In
    case no version is found returns an empty string.

    As there is no standard way to retrieve the version of the shared lib
    this might fail or return wrong info.
    """

    mod_name = mod.__name__
    version = ""

    if mod_name == "GstPbutils":
        t = [mod.PLUGINS_BASE_VERSION_MAJOR, mod.PLUGINS_BASE_VERSION_MINOR,
             mod.PLUGINS_BASE_VERSION_MICRO, mod.PLUGINS_BASE_VERSION_NANO]
        return ".".join(map(str, t))

    version = get_generic_library_version(mod)

    # some cleanup
    version = version.rstrip(".")
    version = version.split("-", 1)[0]

    return version
