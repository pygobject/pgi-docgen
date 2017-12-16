#!/usr/bin/python3
# Copyright 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from __future__ import print_function

import requests

from pgidocgen.util import get_gir_files, parse_gir_shared_libs
from pgidocgen.debug import get_line_numbers_for_name
from pgidocgen.girdata import Project


DATA = {
    "Gtk-3.0": (),
    "Anthy-9000": ("9100h", "", ""),
    #~ "AppStreamGlib-1.0": (
        #~ "0.5.14", "as_bundle_get_sdk",
        #~ "https://github.com/hughsie/appstream-glib/tree/appstream_glib_0_5_14/libappstream-glib/as-bundle.c#L176"),
    "Atk-1.0": (
        "2.20.0", "atk_get_default_registry",
        "https://git.gnome.org/browse/atk/tree/atk/atkregistry.c?h=ATK_2_20_0#n267"),
    "Cally-1.0": (),
    # "Cattle-1.0": ("1.2.0", "cattle_program_new", ""),
    "Champlain-0.12": ("0.12.13",),
    "Clutter-1.0": (),
    "ClutterGdk-1.0": (),
    "ClutterGst-2.0": (),
    "ClutterGst-3.0": (),
    "ClutterX11-1.0": (),
    "Colord-1.0": (
        "1.3.2", "cd_sensor_new",
        "https://github.com/hughsie/colord/blob/1.3.2/lib/colord/cd-sensor.c#L1641"),
    "ColorHug-1.0": (
        "1.3.2", "ch_device_get_spectrum",
        "https://github.com/hughsie/colord/blob/1.3.2/lib/colorhug/ch-device.c#L2146"),
    "EvinceDocument-3.0": (),
    "EvinceView-3.0": (),
    "Fwupd-1.0": (
        "0.7.0", "fwupd_result_set_device_id",
        "https://github.com/hughsie/fwupd/blob/0.7.0/libfwupd/fwupd-result.c#L116"),
    "Gck-1": (
        "3.20.0", "gck_session_open",
        "https://git.gnome.org/browse/gcr/tree/gck/gck-session.c?h=3.20.0#n833"),
    "GData-0.0": (),
    "Gdk-3.0": (),
    "GdkPixbuf-2.0": (
        "2.34.0", "gdk_pixbuf_new_from_file",
        "https://git.gnome.org/browse/gdk-pixbuf/tree/gdk-pixbuf/gdk-pixbuf-io.c?h=2.34.0#n1053"),
    "GdkX11-3.0": (),
    "GES-1.0": (
        "1.8.0", "ges_effect_new",
        "http://cgit.freedesktop.org/gstreamer/gst-editing-services/tree/ges/ges-effect.c?h=1.8.0#n265"),
    # This is buggy..
    #~ "GExiv2-0.10": (
        #~ "0.10.3", "gexiv2_preview_image_new",
        #~ "https://git.gnome.org/browse/gexiv2/tree/gexiv2/gexiv2-startup.cpp?h=gexiv2-0.10.3#n46"),
}


if __name__ == "__main__":
    for namespace, path in get_gir_files().items():
        if DATA.get(namespace):
            version, symbol, res = DATA[namespace]
            p = Project.for_namespace(namespace.split("-")[0])
            assert p.get_tag(version)
            func = p.get_source_func(namespace.split("-")[0], version)
            assert func
            symbols = {}
            for lib in parse_gir_shared_libs(path):
                symbols.update(get_line_numbers_for_name(lib))
            if symbol in symbols:
                symbol_path = symbols[symbol]
                func_res = func(symbol_path)
                assert func_res == res, (func_res, res)
                r = requests.get(res)
                assert r.ok
                assert symbol in r.text, namespace
                print(namespace, res)
            else:
                assert not symbols, symbols
