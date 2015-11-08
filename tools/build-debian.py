#!/usr/bin/python
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
Call these first:

* apt-file update
* sudo apt-get update

"""

import os
import sys
import subprocess
import shutil
import argparse

import apt
import apt_pkg


DEB_BLACKLIST = [
    "gir1.2-panelapplet-4.0",
    "gir1.2-gpaste-2.0",
]

BLACKLIST = [
    # old gstreamer
    "GstController-0.10",
    "GstCheck-0.10",
    "GstAudio-0.10",
    "GstFft-0.10",
    "GstNetbuffer-0.10",
    "GstInterfaces-0.10",
    "GstSdp-0.10",
    "GstRtp-0.10",
    "GstBase-0.10",
    "Gst-0.10",
    "GstPbutils-0.10",
    "GES-0.10",
    "GstTag-0.10",
    "GstVideo-0.10",
    "GstRtspServer-0.10",
    "GstNet-0.10",
    "GstApp-0.10",
    "GstRtsp-0.10",
    "GstRiff-0.10",

    # old gtk
    "Gtk-2.0",
    "Gdk-2.0",
    "GdkX11-2.0",
    'MateDesktop-2.0',
    'PolkitGtkMate-1.0',
    'AtrilView-1.5.0',
    'AtrilDocument-1.5.0',
    'Eom-1.0',

    # broken
    "Gcr-3",
    "GTop-2.0",
    "BraseroMedia-3.1",
    "FolksTelepathy-0.6",
    "Folks-0.6",
    "FolksEds-0.6",
    "Entangle-0.1",
    "Emerillon-0.2",
    "Diodon-1.0",
    "Gee-0.8",
    "Gee-1.0",
    "Grip-1.0",
    "JSCore-3.0",
    "Skk-1.0",
    "SugarExt-1.0",
    "Meta-Muffin.0",
    "libisocodes-1.2.2",

    # criticals.. better skip
    "NMClient-1.0",
    "NMGtk-1.0",

    # depends on one of the above
    "Ganv-1.0",
    "DbusmenuGtk-0.4",
    "MxGtk-1.0",
    "Farstream-0.1",
    "SpiceClientGtk-2.0",
    "GcrUi-3",
    "Caja-2.0",
    "AppIndicator-0.1",
    "MatePanelApplet-4.0",
    "ClutterGst-1.0",
    "BraseroBurn-3.1",
    "Listaller-0.5",
    "v_sim-3.7",
    "FolksDummy-0.6",
]

BUILD = ['AccountsService-1.0', 'Anjuta-3.0', 'AppIndicator3-0.1', 'Atk-1.0',
'Atspi-2.0', 'Cally-1.0', 'Caribou-1.0', 'Champlain-0.12', 'Cheese-3.0',
'Clinica-0.3', 'Clutter-1.0', 'ClutterGdk-1.0', 'ClutterGst-2.0',
'ClutterX11-1.0', 'Cogl-1.0', 'Cogl-2.0', 'CoglPango-1.0', 'ColorHug-1.0',
'Colord-1.0', 'ColordGtk-1.0', 'CryptUI-0.0', 'DBus-1.0', 'DBusGLib-1.0',
'Dbusmenu-0.4', 'DbusmenuGtk3-0.4', 'Dee-1.0', 'EBook-1.2',
'EBookContacts-1.2', 'EDataServer-1.2', 'EvinceDocument-3.0',
'EvinceView-3.0', 'Farstream-0.2', 'Fcitx-1.0', 'GConf-2.0', 'GData-0.0',
'GDesktopEnums-3.0', 'GES-1.0', 'GExiv2-0.10', 'GIRepository-2.0', 'GL-1.0',
'GLib-2.0', 'GMenu-3.0', 'GModule-2.0', 'GObject-2.0', 'GOffice-0.10',
'GSSDP-1.0', 'GUPnP-1.0', 'GUPnPAV-1.0', 'GUPnPDLNA-2.0', 'GUPnPDLNAGst-2.0',
'GUPnPIgd-1.0', 'GUdev-1.0', 'GUsb-1.0', 'GWeather-3.0', 'GXPS-0.1', 'Gck-1',
'Gda-5.0', 'Gdk-3.0', 'GdkPixbuf-2.0', 'GdkX11-3.0', 'Gdl-3', 'Gdm-1.0',
'GeocodeGlib-1.0', 'Gio-2.0', 'Gkbd-3.0', 'Gladeui-2.0', 'GnomeBluetooth-1.0',
'GnomeDesktop-3.0', 'GnomeKeyring-1.0', 'Goa-1.0', 'Grl-0.2', 'GrlNet-0.2',
'Gsf-1', 'Gst-1.0', 'GstAllocators-1.0', 'GstApp-1.0', 'GstAudio-1.0',
'GstBase-1.0', 'GstCheck-1.0', 'GstController-1.0', 'GstFft-1.0',
'GstNet-1.0', 'GstPbutils-1.0', 'GstRtp-1.0', 'GstRtsp-1.0', 'GstSdp-1.0',
'GstTag-1.0', 'GstVideo-1.0', 'Gtk-3.0', 'GtkChamplain-0.12',
'GtkClutter-1.0', 'GtkSource-3.0', 'GtkSpell-3.0', 'Gucharmap-2.90',
'IBus-1.0', 'Indicate-0.7', 'Itl-1.0', 'JavaScriptCore-3.0', 'Json-1.0',
'Keybinder-0.0', 'LangTag-0.5', 'Libosinfo-1.0', 'LibvirtGConfig-1.0',
'LibvirtGLib-1.0', 'LibvirtGObject-1.0', 'LunarDate-2.0', 'MPID-3.0',
'Mx-1.0', 'Nautilus-3.0', 'Nemo-3.0', 'NetworkManager-1.0', 'Notify-0.7',
'PackageKitGlib-1.0', 'Pango-1.0', 'PangoCairo-1.0', 'PangoFT2-1.0',
'PangoXft-1.0', 'Peas-1.0', 'PeasGtk-1.0', 'Polkit-1.0', 'PolkitAgent-1.0',
'Poppler-0.18', 'RB-3.0', 'Rest-0.7', 'RestExtras-0.7', 'Rsvg-2.0',
'Secret-1', 'Soup-2.4', 'SoupGNOME-2.4', 'SpiceClientGLib-2.0',
'SpiceClientGtk-3.0', 'SugarGestures-1.0', 'TelepathyGLib-0.12',
'TelepathyLogger-0.2', 'TotemPlParser-1.0', 'Tracker-1.0',
'TrackerControl-1.0', 'TrackerMiner-1.0', 'UDisks-2.0', 'UMockdev-1.0',
'UPowerGlib-1.0', 'Vte-2.91', 'WebKit-3.0', 'WebKit2-3.0', 'Wnck-3.0',
'Xkl-1.0', 'Zeitgeist-2.0', 'Zpj-0.0', 'cairo-1.0', 'fontconfig-2.0',
'freetype2-2.0', 'libxml2-2.0', 'xfixes-4.0', 'xft-2.0', 'xlib-2.0',
'xrandr-1.3', "CoglPango-2.0", "GFBGraph-0.2", "GrlPls-0.2", "Guestfs-1.0",
"HarfBuzz-0.0", "InputPad-1.0", "Keybinder-3.0", "LightDM-1", "MateMenu-2.0",
"MediaArt-1.0", "Midgard-10.05", "OsmGpsMap-1.0", "Totem-1.0", "Uhm-0.0",
"AppStreamGlib-1.0", "CDesktopEnums-3.0", "CMenu-3.0", "CinnamonDesktop-3.0",
"ModemManager-1.0", "Evd-0.1", "Cattle-1.0", "GCab-1.0", "GPaste-1.0",
"GVnc-1.0", "GVncPulse-1.0", "Ggit-1.0", "GtkVnc-2.0", "JavaScriptCore-4.0",
"SocialWebClient-0.25", "WebKit2-4.0", "WebKit2WebExtension-4.0", "NM-1.0",
"GstGL-1.0", "GstInsertBin-1.0", "GstMpegts-1.0", 'Anthy-9000', 'Vte-2.90',
'MediaArt-2.0', 'Gdict-1.0', 'CoglGst-2.0', 'GstRtspServer-1.0',
'ClutterGst-3.0', 'Gom-1.0', 'Limba-1.0', 'PanelApplet-5.0', 'AppStream-0.8',
'Abi-3.0', 'Gnm-1.12', 'Hkl-4.0', 'Libmsi-1.0', 'Vips-8.0', 'GooCanvas-2.0',
'GSound-1.0', 'Accounts-1.0', 'Signon-1.0', 'Fwupd-1.0'
]


def get_typelibs():
    """Note that this also finds things in stable/experimental, so
    apt-get downloading these might not give you a typelib file.
    """

    cache = apt.Cache()
    cache.open(None)

    typelibs = {}
    to_install = set()

    data = subprocess.check_output(["apt-file", "search", ".typelib"])
    for line in data.strip().splitlines():
        package, path = line.split(": ", 1)
        if package in DEB_BLACKLIST:
            continue
        if path.startswith("/usr/lib/x86_64-linux-gnu/girepository-1.0/") or \
                path.startswith("/usr/lib/girepository-1.0/"):
            if cache[package].candidate is None:
                continue
            if not cache[package].is_installed:
                to_install.add(package)
            if not os.path.exists(path):
                continue
            name = os.path.splitext(os.path.basename(path))[0]
            l = typelibs.setdefault(package, [])
            if name not in l:
                l.append(name)

    cache.close()

    if to_install:
        print "Not all typelibs installed:\n"
        print "sudo aptitude install " + " ".join(sorted(to_install))
        raise SystemExit(1)

    return typelibs


def get_girs():
    """Note that this also finds things in stable/experimental, so
    apt-get downloading these might not give you a gir file.
    """

    cache = apt.Cache()
    cache.open(None)

    girs = {}
    data = subprocess.check_output(["apt-file", "search", ".gir"])
    for line in data.strip().splitlines():
        package, path = line.split(": ", 1)
        if cache[package].candidate is None:
            continue
        if path.startswith("/usr/share/gir-1.0/"):
            name = os.path.splitext(os.path.basename(path))[0]
            l = girs.setdefault(package, [])
            if name not in l:
                l.append(name)
    cache.close()
    return girs


def reverse_mapping(d):
    r = {}
    for key, values in d.iteritems():
        for value in values:
            assert value not in r
            r[value] = key
    return r


def compare_deb_packages(a, b):
    va = subprocess.check_output(["dpkg", "--field", a, "Version"]).strip()
    vb = subprocess.check_output(["dpkg", "--field", b, "Version"]).strip()
    return apt_pkg.version_compare(va, vb)


def fetch_girs(girs, dest):
    dest = os.path.abspath(dest)
    assert not os.path.exists(dest)
    os.mkdir(dest)

    tmp_root = os.path.join(dest, "temp_root")
    tmp_download = os.path.join(dest, "tmp_download")
    dst = os.path.join(dest, "gir-1.0")

    print "Download packages.."
    cache = apt.Cache()
    cache.open(None)
    os.mkdir(tmp_download)
    # install anything that is a candidate or older
    # (is versions really ordered?)
    for name in girs:
        package = cache[name]
        ok = False
        for version in package.versions:
            if ok or package.candidate == version:
                ok = True
                try:
                    # XXX: This fails in various ways unrelated to the actual
                    # download action
                    version.fetch_binary(tmp_download)
                except Exception as e:
                    print e
    cache.close()

    print "Extracting packages.."

    # sort, so older girs get replaced
    entries = [os.path.join(tmp_download, e) for e in os.listdir(tmp_download)]
    entries.sort(cmp=compare_deb_packages)

    os.mkdir(dst)
    for path in entries:
        subprocess.check_call(["dpkg" , "-x", path, tmp_root])
        base_src = os.path.join(tmp_root, "usr", "share", "gir-1.0")
        if not os.path.isdir(base_src):
            continue
        for e in os.listdir(base_src):
            src = os.path.join(base_src, e)
            shutil.copy(src, dst)
        shutil.rmtree(tmp_root)


def fetch_girs_cached():
    temp_data = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "_temp_data_dir")
    if not os.path.exists(temp_data):
        print "find girs.."
        girs = get_girs()
        print "fetch and extract debian packages.."
        fetch_girs(girs, temp_data)
    return temp_data


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--devhelp', action='store_true')
    args = parser.parse_args(argv[1:])

    print "[don't forget to apt-file update/apt-get update!]"

    print "find typelibs.."
    typelibs = get_typelibs()

    data_dir = fetch_girs_cached()
    gir_dir = os.path.join(data_dir, "gir-1.0")
    gir_list = [os.path.splitext(e)[0] for e in os.listdir(gir_dir)]

    rtypelibs = reverse_mapping(typelibs)
    print "Missing gir files: %r" % sorted(set(rtypelibs) - set(gir_list))
    print "Missing typelib files: %r" % sorted(set(gir_list) - set(rtypelibs))
    can_build = sorted(set(gir_list) & set(rtypelibs))
    print "%d ready to build" % len(can_build)

    assert not (set(BLACKLIST) & set(BUILD))

    unknown_build = set(BLACKLIST) - set(can_build)
    assert not unknown_build, unknown_build
    can_build = set(can_build) - set(BLACKLIST)
    print "%d ready to build after blacklisting" % len(can_build)

    unknown_build = set(BUILD) - set(can_build)
    assert not unknown_build, unknown_build
    missing_build = set(can_build) - set(BUILD)
    assert not missing_build, missing_build

    os.environ["XDG_DATA_DIRS"] = data_dir

    if args.devhelp:
        subprocess.check_call(
            ["python", "./pgi-docgen.py", "_devhelp"] + BUILD)
        subprocess.check_call(
            ["python", "./pgi-docgen-build.py", "--devhelp",
             "_devhelp", "_devhelp/_build"])
    else:
        subprocess.check_call(
            ["python", "./pgi-docgen.py", "_docs"] + BUILD)
        subprocess.check_call(
            ["python", "./pgi-docgen-build.py", "_docs", "_docs/_build"])


if __name__ == "__main__":
    main(sys.argv)
