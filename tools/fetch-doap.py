#!/usr/bin/python
# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
from multiprocessing import Pool

import requests

from pgidocgen.util import get_gir_files


LIBS = {
    'https://git.gnome.org/browse/librest/plain/librest.doap':
        ['RestExtras-0.7', 'Rest-0.7'],
    'https://git.gnome.org/browse/gtk+/plain/gtk+.doap':
        ['Gtk-3.0', 'GdkX11-3.0', 'Gdk-3.0', 'Gdk-2.0', 'GdkX11-2.0',
         'Gtk-2.0'],
    'http://cgit.freedesktop.org/gstreamer/gstreamer/plain/gstreamer.doap':
        ['GstController-1.0', 'GstNet-1.0', 'Gst-1.0', 'GstCheck-1.0',
         'GstBase-1.0', 'Gst-0.10', 'GstBase-0.10', 'GstCheck-0.10',
         'GstController-0.10', 'GstNet-0.10'],
    'http://cgit.freedesktop.org/gstreamer/gst-plugins-base/plain/gst-plugins-base.doap':
        ['GstRtsp-1.0', 'GstPbutils-1.0', 'GstApp-1.0', 'GstRtp-1.0',
         'GstAllocators-1.0', 'GstFft-1.0', 'GstVideo-1.0', 'GstAudio-1.0',
         'GstRiff-1.0', 'GstSdp-1.0', 'GstTag-1.0', 'GstAudio-0.10',
         'GstApp-0.10',  'GstFft-0.10', 'GstInterfaces-0.10',
         'GstPbutils-0.10', 'GstRiff-0.10', 'GstRtp-0.10', 'GstRtsp-0.10',
         'GstRtspServer-0.10', 'GstSdp-0.10', 'GstTag-0.10',
         'GstNetbuffer-0.10', 'GstVideo-0.10'],
    'https://git.gnome.org/browse/glib/plain/glib.doap':
        ['GLib-2.0', 'GObject-2.0', 'Gio-2.0'],
    'https://git.gnome.org/browse/atk/plain/atk.doap':
        ['Atk-1.0'],
    'https://git.gnome.org/browse/cogl/plain/cogl.doap':
        ['Cogl-1.0', 'CoglPango-1.0', 'Cogl-2.0', 'CoglPango-2.0'],
    'https://git.gnome.org/browse/gupnp-av/plain/gupnp-av.doap':
        ['GUPnPAV-1.0'],
    'https://git.gnome.org/browse/cheese/plain/cheese.doap':
        ['Cheese-3.0'],
    'https://git.gnome.org/browse/libgsf/plain/libgsf.doap':
        ['Gsf-1'],
    'https://git.gnome.org/browse/libpeas/plain/libpeas.doap':
        ['Peas-1.0', 'PeasGtk-1.0'],
    'https://git.gnome.org/browse/gdl/plain/gdl.doap':
        ['Gdl-3'],
    'https://git.gnome.org/browse/anjuta/plain/anjuta.doap':
        ['Anjuta-3.0'],
    'https://git.gnome.org/browse/gupnp-igd/plain/gupnp-igd.doap':
        ['GUPnPIgd-1.0'],
    'https://git.gnome.org/browse/libsecret/plain/libsecret.doap':
        ['SecretUnstable-0', 'Secret-1'],
    'https://git.gnome.org/browse/nautilus/plain/nautilus.doap':
        ['Nautilus-3.0'],
    'https://git.gnome.org/browse/gupnp/plain/gupnp.doap':
        ['GUPnP-1.0'],
    'https://git.gnome.org/browse/rhythmbox/plain/rhythmbox.doap':
        ['MPID-3.0', 'RB-3.0'],
    'https://raw.github.com/hughsie/colord/master/colord.doap':
        ['Colord-1.0', 'ColordGtk-1.0'],
    'https://git.gnome.org/browse/gobject-introspection/plain/gobject-introspection.doap':
        ['DBus-1.0', 'GModule-2.0', 'Gio-2.0', 'xrandr-1.3',
         'GIRepository-2.0', 'GObject-2.0', 'fontconfig-2.0', 'freetype2-2.0',
         'libxml2-2.0', 'GLib-2.0', 'xlib-2.0', 'DBusGLib-1.0', 'cairo-1.0',
         'xft-2.0', 'GL-1.0', 'xfixes-4.0'],
    'https://git.gnome.org/browse/gconf/plain/gconf.doap':
        ['GConf-2.0'],
    'https://git.gnome.org/browse/geocode-glib/plain/geocode-glib.doap':
        ['GeocodeGlib-1.0'],
    'https://git.gnome.org/browse/libgovirt/plain/libgovirt.doap':
        ['LibvirtGConfig-1.0', 'LibvirtGLib-1.0', 'LibvirtGObject-1.0'],
    'https://git.gnome.org/browse/libgdata/plain/libgdata.doap':
        ['GData-0.0'],
    'https://git.gnome.org/browse/grilo/plain/grilo.doap':
        ['GrlNet-0.2', 'Grl-0.2'],
    'https://git.gnome.org/browse/grilo-plugins/plain/grilo-plugins.doap':
        ['GrlPls-0.2'],
    'https://git.gnome.org/browse/gexiv2/plain/gexiv2.doap':
        ['GExiv2-0.4', 'GExiv2-0.10'],
    'https://git.gnome.org/browse/folks/plain/folks.doap':
        ['Folks-0.6', 'FolksEds-0.6', 'FolksTelepathy-0.6'],
    'https://git.gnome.org/browse/at-spi2-core/plain/at-spi2-core.doap':
        ['Atspi-2.0'],
    'https://git.gnome.org/browse/caribou/plain/caribou.doap':
        ['Caribou-1.0'],
    'https://git.gnome.org/browse/clutter/plain/clutter.doap':
        ['ClutterGdk-1.0', 'Clutter-1.0', 'ClutterX11-1.0', 'Cally-1.0'],
    'https://git.gnome.org/browse/clutter-gst/plain/clutter-gst.doap':
        ['ClutterGst-2.0', 'ClutterGst-1.0'],
    'https://git.gnome.org/browse/clutter-gtk/plain/clutter-gtk.doap':
        ['GtkClutter-1.0'],
    'https://git.gnome.org/browse/evince/plain/evince.doap':
        ['EvinceDocument-3.0', 'EvinceView-3.0'],
    'https://git.gnome.org/browse/evolution-data-server/plain/evolution-data-server.doap':
        ['EDataServer-1.2', 'EBook-1.2', 'EBookContacts-1.2'],
    'https://git.gnome.org/browse/gcr/plain/gcr.doap':
        ['Gck-1', 'Gcr-3', 'GcrUi-3'],
    'https://git.gnome.org/browse/gdm/plain/gdm.doap':
        ['Gdm-1.0'],
    'https://git.gnome.org/browse/gdk-pixbuf/plain/gdk-pixbuf.doap':
        ['GdkPixbuf-2.0'],
    'https://git.gnome.org/browse/gnome-bluetooth/plain/gnome-bluetooth.doap':
        ['GnomeBluetooth-1.0'],
    'https://git.gnome.org/browse/gnome-desktop/plain/gnome-desktop.doap':
        ['GnomeDesktop-3.0'],
    'https://git.gnome.org/browse/gnome-menus/plain/gnome-menus.doap':
        ['GMenu-3.0'],
    'https://git.gnome.org/browse/gnome-online-accounts/plain/gnome-online-accounts.doap':
        ['Goa-1.0'],
    'https://git.gnome.org/browse/gnome-panel/plain/gnome-panel.doap':
        ['PanelApplet-4.0'],
    'https://git.gnome.org/browse/gsettings-desktop-schemas/plain/gsettings-desktop-schemas.doap':
        ['GDesktopEnums-3.0'],
    'https://git.gnome.org/browse/gssdp/plain/gssdp.doap':
        ['GSSDP-1.0'],
    'https://git.gnome.org/browse/gtksourceview/plain/gtksourceview.doap':
        ['GtkSource-3.0'],
    'https://git.gnome.org/browse/gtk-vnc/plain/gtk-vnc.doap':
        ['GVncPulse-1.0', 'GtkVnc-2.0', 'GVnc-1.0'],
    'https://git.gnome.org/browse/gucharmap/plain/gucharmap.doap':
        ['Gucharmap-2.90'],
    'https://git.gnome.org/browse/gupnp-dlna/plain/gupnp-dlna.doap':
        ['GUPnPDLNAGst-2.0', 'GUPnPDLNA-2.0'],
    'https://git.gnome.org/browse/json-glib/plain/json-glib.doap':
        ['Json-1.0'],
    'https://git.gnome.org/browse/libchamplain/plain/libchamplain.doap':
        ['Champlain-0.12', 'GtkChamplain-0.12'],
    'https://git.gnome.org/browse/libcryptui/plain/libcryptui.doap':
        ['CryptUI-0.0'],
    'https://git.gnome.org/browse/libgda/plain/libgda.doap':
        ['Gda-5.0'],
    'https://git.gnome.org/browse/libgee/plain/libgee.doap':
        ['Gee-0.8'],
    'https://git.gnome.org/browse/libgnomekbd/plain/libgnomekbd.doap':
        ['Gkbd-3.0'],
    'https://git.gnome.org/browse/gnome-keyring/plain/gnome-keyring.doap':
        ['GnomeKeyring-1.0'],
    'https://git.gnome.org/browse/libgweather/plain/libgweather.doap':
        ['GWeather-3.0'],
    'https://git.gnome.org/browse/libgxps/plain/libgxps.doap':
        ['GXPS-0.1'],
    'https://git.gnome.org/browse/libnotify/plain/libnotify.doap':
        ['Notify-0.7'],
    'https://git.gnome.org/browse/librsvg/plain/librsvg.doap':
        ['Rsvg-2.0'],
    'https://git.gnome.org/browse/libsocialweb/plain/libsocialweb.doap':
        ['SocialWebClient-0.25'],
    'https://git.gnome.org/browse/libsoup/plain/libsoup.doap':
        ['SoupGNOME-2.4', 'Soup-2.4'],
    'https://git.gnome.org/browse/libwnck/plain/libwnck.doap':
        ['Wnck-3.0'],
    'https://git.gnome.org/browse/libzapojit/plain/libzapojit.doap':
        ['Zpj-0.0'],
    'https://gitorious.org/packagekit/packagekit/raw/PackageKit.doap':
        ['PackageKitGlib-1.0', 'PackageKitPlugin-1.0'],
    'https://git.gnome.org/browse/pango/plain/pango.doap':
        ['PangoCairo-1.0', 'PangoXft-1.0', 'PangoFT2-1.0', 'Pango-1.0'],
    'https://git.gnome.org/browse/totem-pl-parser/plain/totem-pl-parser.doap':
        ['TotemPlParser-1.0'],
    'https://git.gnome.org/browse/tracker/plain/tracker.doap':
        ['TrackerMiner-0.16', 'TrackerExtract-0.16', 'Tracker-0.16',
         'TrackerMiner-1.0', 'Tracker-1.0', 'TrackerControl-1.0'],
    'https://git.gnome.org/browse/vte/plain/vte.doap':
        ['Vte-2.90'],
    'http://cgit.freedesktop.org/gstreamer/gst-editing-services/plain/gst-editing-services.doap':
        ['GES-1.0', 'GES-0.10'],
    'https://git.gnome.org/browse/brasero/plain/brasero.doap':
        ['BraseroBurn-3.1', 'BraseroMedia-3.1'],
    'https://git.gnome.org/browse/goffice/plain/goffice.doap':
        ['GOffice-0.10'],
    'https://git.gnome.org/browse/glade/plain/glade.doap':
        ['Gladeui-2.0'],
    'https://git.gnome.org/browse/totem/plain/totem.doap':
        ['Totem-1.0'],
    'https://git.gnome.org/browse/libgtop/plain/libgtop.doap':
        ['GTop-2.0'],
    'https://git.gnome.org/browse/libmediaart/plain/libmediaart.doap':
        ['MediaArt-1.0'],
    'https://git.gnome.org/browse/gegl/plain/gegl.doap':
        ['Gegl-0.3'],
}


def fetch(args):
    url, data = args
    print url
    resp = requests.get(url)
    return resp.content, data


if __name__ == '__main__':
    ns_list = set(get_gir_files().keys())
    for values in LIBS.values():
        ns_list -= set(values)

    print "Missing:"
    print sorted(ns_list)

    pool = Pool(20)
    for content, ns_list in pool.imap_unordered(fetch, LIBS.items()):
        for ns in ns_list:
            with open(os.path.join('data', 'doap', ns) + ".doap", 'wb') as h:
                h.write(content)
