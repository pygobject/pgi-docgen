#!/usr/bin/python

import sys
import subprocess

from pgidocgen.util import get_gir_files
from pgidocgen.namespace import get_namespace


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

    # broken
    "Gcr-3",
    "GTop-2.0",
    "BraseroMedia-3.1",
    "Clinica-0.2",
    "Gnm-1.12",
    "FolksTelepathy-0.6",
    "Folks-0.6",
    "FolksEds-0.6",
    "Entangle-0.1",
    "Emerillon-0.2",
    "Diodon-1.0",
    "Gee-0.8",
    "Gee-1.0",
    "Grip-1.0",
    "JSCore-1.0",
    "JSCore-3.0",
    "Skk-1.0",
    "SugarExt-1.0",
    "Urfkill-0.5",
    "win32-1.0",
    "Meta-3.0",
    "Meta-Muffin.0",
    "libisocodes-1.2.1",
    "JavaScriptCore-1.0",

    # criticals.. better skip
    "Gwibber-0.1",
    "NMClient-1.0",
    "NMGtk-1.0",

    # depends on one of the above
    "GUPnPDLNA-1.0",
    "Ganv-1.0",
    "DbusmenuGtk-0.4",
    "MxGtk-1.0",
    "Farstream-0.1",
    "SpiceClientGtk-2.0",
    "GcrUi-3",
    "Caja-2.0",
    "AppIndicator-0.1",
    "WebKit-1.0",
    "MatePanelApplet-4.0",
    "ClutterGst-1.0",
    "GwibberGtk-0.1",
    "BraseroBurn-3.1",
    "Listaller-0.5",
    "v_sim-3.7",
    "FolksDummy-0.6",
]

BUILD = ['AccountsService-1.0', 'Anjuta-3.0',
'AppIndicator3-0.1', 'Atk-1.0', 'Atspi-2.0', 'Cally-1.0', 'Caribou-1.0', 
'Champlain-0.12', 'Cheese-3.0', 'Clinica-0.3', 'Clutter-1.0', 
'ClutterGdk-1.0', 'ClutterGst-2.0', 'ClutterX11-1.0', 'Cogl-1.0', 'Cogl-2.0', 
'CoglPango-1.0', 'ColorHug-1.0', 'Colord-1.0', 'ColordGtk-1.0', 'CryptUI-0.0', 
'DBus-1.0', 'DBusGLib-1.0', 'Dbusmenu-0.4', 'DbusmenuGtk3-0.4', 'Dee-1.0', 
'EBook-1.2', 'EBookContacts-1.2', 'EDataServer-1.2', 'EvinceDocument-3.0', 
'EvinceView-3.0', 'Farstream-0.2', 'Fcitx-1.0', 'GConf-2.0', 'GData-0.0', 
'GDesktopEnums-3.0', 'GES-1.0', 'GExiv2-0.10', 'GIRepository-2.0', 'GL-1.0', 
'GLib-2.0', 'GMenu-3.0', 'GModule-2.0', 'GObject-2.0', 'GOffice-0.10', 
'GSSDP-1.0', 'GUPnP-1.0', 'GUPnPAV-1.0', 'GUPnPDLNA-2.0', 'GUPnPDLNAGst-2.0', 
'GUPnPIgd-1.0', 'GUdev-1.0', 'GUsb-1.0', 
'GWeather-3.0', 'GXPS-0.1', 'Gck-1', 'Gda-5.0', 'Gdk-3.0', 'GdkPixbuf-2.0', 
'GdkX11-3.0', 'Gdl-3', 'Gdm-1.0', 'GeocodeGlib-1.0', 'Gio-2.0', 'Gkbd-3.0', 
'Gladeui-2.0', 'GnomeBluetooth-1.0', 'GnomeDesktop-3.0', 'GnomeKeyring-1.0', 
'Goa-1.0', 'Grl-0.2', 'GrlNet-0.2', 'Gsf-1', 'Gst-1.0', 'GstAllocators-1.0', 
'GstApp-1.0', 'GstAudio-1.0', 'GstBase-1.0', 'GstCheck-1.0', 
'GstController-1.0', 'GstFft-1.0', 'GstNet-1.0', 'GstPbutils-1.0', 
'GstRiff-1.0', 'GstRtp-1.0', 'GstRtsp-1.0', 'GstSdp-1.0', 'GstTag-1.0', 
'GstVideo-1.0', 'Gtk-3.0', 'GtkChamplain-0.12', 'GtkClutter-1.0', 
'GtkSource-3.0', 'GtkSpell-3.0', 'Gucharmap-2.90', 'IBus-1.0', 
'Indicate-0.7', 'Itl-1.0', 'JavaScriptCore-3.0', 'Json-1.0', 'Keybinder-0.0', 
'LangTag-0.5', 'Libosinfo-1.0', 'LibvirtGConfig-1.0', 'LibvirtGLib-1.0', 
'LibvirtGObject-1.0', 'LunarDate-2.0', 'MPID-3.0', 'Mx-1.0', 'Nautilus-3.0', 
'Nemo-3.0', 'NetworkManager-1.0', 'Notify-0.7', 'PackageKitGlib-1.0', 
'PanelApplet-4.0', 'Pango-1.0', 'PangoCairo-1.0', 
'PangoFT2-1.0', 'PangoXft-1.0', 'Peas-1.0', 'PeasGtk-1.0', 'Polkit-1.0', 
'PolkitAgent-1.0', 'Poppler-0.18', 'RB-3.0', 'Rest-0.7', 'RestExtras-0.7', 
'Rsvg-2.0', 'Secret-1', 'Soup-2.4', 'SoupGNOME-2.4', 
'SpiceClientGLib-2.0', 'SpiceClientGtk-3.0', 'SugarGestures-1.0', 
'TelepathyGLib-0.12', 'TelepathyLogger-0.2', 'TotemPlParser-1.0', 
'Tracker-1.0', 'TrackerControl-1.0', 'TrackerMiner-1.0', 'UDisks-2.0', 
'UMockdev-1.0', 'UPowerGlib-1.0', 'Vte-2.91', 'WebKit-3.0', 'WebKit2-3.0',
'Wnck-3.0', 'Xkl-1.0', 'Zeitgeist-2.0', 'Zpj-0.0', 'cairo-1.0', 
'fontconfig-2.0', 'freetype2-2.0', 'libxml2-2.0', 'xfixes-4.0', 'xft-2.0', 
'xlib-2.0', 'xrandr-1.3', "CoglPango-2.0", "GFBGraph-0.2", 
"GrlPls-0.2", "Guestfs-1.0", "HarfBuzz-0.0", 
"InputPad-1.0", "Keybinder-3.0", "LightDM-1", 
"MateMenu-2.0", "MediaArt-1.0", "Midgard-10.05", "OsmGpsMap-1.0", "Totem-1.0", 
 "Uhm-0.0", "AppStream-0.7", "AppStreamGlib-1.0",
"CDesktopEnums-3.0", "CMenu-3.0", "CinnamonDesktop-3.0", "ModemManager-1.0", 
"Evd-0.1", "Cattle-1.0", "GCab-1.0", 
"GPaste-1.0", "GVnc-1.0", "GVncPulse-1.0", "Ggit-1.0", "GtkVnc-2.0", 
"JavaScriptCore-4.0", "SocialWebClient-0.25", 
"WebKit2-4.0", "WebKit2WebExtension-4.0", "NM-1.0", "GstGL-1.0",
"GstInsertBin-1.0", "GstMpegts-1.0",
]


def print_missing():
    """print modules that are present but not included in the build list
    or the blacklist
    """

    print "Building %d modules.." % len(BUILD)
    print "Check if all girs are present..."

    girs = get_gir_files()

    missing = set(BUILD) - set(girs.keys())
    if missing:
        print "Missing girs: %r" % missing

    bl_depend = set()

    if "--no-check" in sys.argv[1:]:
        return

    print "Check if there are unknown girs..."
    blacklist = set(BLACKLIST)
    unlisted = set()
    for key, path in girs.items():
        if key not in BUILD and key not in BLACKLIST:
            ns = get_namespace(*key.split("-"))
            deps = set(["-".join(d) for d in ns.get_all_dependencies()])
            if deps & blacklist:
                bl_depend.add(key)
                continue
            unlisted.add(key)

    if bl_depend:
        print "Depending on blacklisted modules; add them to the black list:"
        for key in bl_depend:
            print "\"%s\"," % key

    if unlisted:
        print ("The following girs are available but not in the build list; "
               "please add or black list them:")
        for key in sorted(unlisted):
            print "\"%s\"," % key

    if unlisted or bl_depend:
        raise SystemExit(1)


if __name__ == "__main__":
    print_missing()
    subprocess.check_call(["python", "./pgi-docgen.py", "_docs"] + BUILD)
    subprocess.check_call(
        ["python", "./pgi-docgen-build.py", "_docs", "_docs/_build"])
