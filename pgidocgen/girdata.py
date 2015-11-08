# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""Database containing additional optional info about common gir files"""

import re
from collections import namedtuple


Project = P = namedtuple('Project', ['namespaces', 'doap'])
"""A project is roughly something which gets released at the same time and
has the same release version number. In most cases one git repo.
The namespaces might not actually be included in the project but the libraries
of the GIR are (e.g. GLib-2.0.gir is in libgirepository, but it's part of GLib)
"""


PROJECTS = [
    P(['Goa'], 'https://git.gnome.org/browse/gnome-online-accounts/plain/gnome-online-accounts.doap'),
    P(['GnomeDesktop'], 'https://git.gnome.org/browse/gnome-desktop/plain/gnome-desktop.doap'),
    P(['Gladeui'], 'https://git.gnome.org/browse/glade/plain/glade.doap'),
    P(['GVnc', 'GVncPulse', 'GtkVnc'], 'https://git.gnome.org/browse/gtk-vnc/plain/gtk-vnc.doap'),
    P(['Peas', 'PeasGtk'], 'https://git.gnome.org/browse/libpeas/plain/libpeas.doap'),
    P(['CryptUI'], 'https://git.gnome.org/browse/libcryptui/plain/libcryptui.doap'),
    P(['DBus', 'DBusGLib', 'GIRepository', 'GL', 'cairo', 'fontconfig', 'freetype2', 'libxml2', 'win32', 'xfixes', 'xft', 'xlib', 'xrandr'], 'https://git.gnome.org/browse/gobject-introspection/plain/gobject-introspection.doap'),
    P(['EvinceDocument', 'EvinceView'], 'https://git.gnome.org/browse/evince/plain/evince.doap'),
    P(['PackageKitGlib', 'PackageKitPlugin'], 'https://raw.githubusercontent.com/hughsie/PackageKit/master/PackageKit.doap'),
    P(['Gkbd'], 'https://git.gnome.org/browse/libgnomekbd/plain/libgnomekbd.doap'),
    P(['GtkClutter'], 'https://git.gnome.org/browse/clutter-gtk/plain/clutter-gtk.doap'),
    P(['GDesktopEnums'], 'https://git.gnome.org/browse/gsettings-desktop-schemas/plain/gsettings-desktop-schemas.doap'),
    P(['GExiv2'], 'https://git.gnome.org/browse/gexiv2/plain/gexiv2.doap'),
    P(['Rsvg'], 'https://git.gnome.org/browse/librsvg/plain/librsvg.doap'),
    P(['GnomeKeyring'], 'https://git.gnome.org/browse/gnome-keyring/plain/gnome-keyring.doap'),
    P(['Atk'], 'https://git.gnome.org/browse/atk/plain/atk.doap'),
    P(['GtkSource'], 'https://git.gnome.org/browse/gtksourceview/plain/gtksourceview.doap'),
    P(['GTop'], 'https://git.gnome.org/browse/libgtop/plain/libgtop.doap'),
    P(['Rest', 'RestExtras'], 'https://git.gnome.org/browse/librest/plain/librest.doap'),
    P(['Gck', 'Gcr', 'GcrUi'], 'https://git.gnome.org/browse/gcr/plain/gcr.doap'),
    P(['Notify'], 'https://git.gnome.org/browse/libnotify/plain/libnotify.doap'),
    P(['GUPnPIgd'], 'https://git.gnome.org/browse/gupnp-igd/plain/gupnp-igd.doap'),
    P(['SocialWebClient'], 'https://git.gnome.org/browse/libsocialweb/plain/libsocialweb.doap'),
    P(['PanelApplet'], 'https://git.gnome.org/browse/gnome-panel/plain/gnome-panel.doap'),
    P(['GUPnP'], 'https://git.gnome.org/browse/gupnp/plain/gupnp.doap'),
    P(['GSSDP'], 'https://git.gnome.org/browse/gssdp/plain/gssdp.doap'),
    P(['GOffice'], 'https://git.gnome.org/browse/goffice/plain/goffice.doap'),
    P(['Cheese'], 'https://git.gnome.org/browse/cheese/plain/cheese.doap'),
    P(['Pango', 'PangoCairo', 'PangoFT2', 'PangoXft'], 'https://git.gnome.org/browse/pango/plain/pango.doap'),
    P(['Gda'], 'https://git.gnome.org/browse/libgda/plain/libgda.doap'),
    P(['GConf'], 'https://git.gnome.org/browse/gconf/plain/gconf.doap'),
    P(['Soup', 'SoupGNOME'], 'https://git.gnome.org/browse/libsoup/plain/libsoup.doap'),
    P(['MPID', 'RB'], 'https://git.gnome.org/browse/rhythmbox/plain/rhythmbox.doap'),
    P(['Gegl'], 'https://git.gnome.org/browse/gegl/plain/gegl.doap'),
    P(['Grl', 'GrlNet'], 'https://git.gnome.org/browse/grilo/plain/grilo.doap'),
    P(['GMenu'], 'https://git.gnome.org/browse/gnome-menus/plain/gnome-menus.doap'),
    P(['Json'], 'https://git.gnome.org/browse/json-glib/plain/json-glib.doap'),
    P(['GstAllocators', 'GstApp', 'GstAudio', 'GstFft', 'GstInterfaces', 'GstNetbuffer', 'GstPbutils', 'GstRiff', 'GstRtp', 'GstRtsp', 'GstRtspServer', 'GstSdp', 'GstTag', 'GstVideo'], 'http://cgit.freedesktop.org/gstreamer/gst-plugins-base/plain/gst-plugins-base.doap'),
    P(['GUdev'], 'https://git.gnome.org/browse/libgudev/plain/libgudev.doap'),
    P(['Champlain', 'GtkChamplain'], 'https://git.gnome.org/browse/libchamplain/plain/libchamplain.doap'),
    P(['Secret', 'SecretUnstable'], 'https://git.gnome.org/browse/libsecret/plain/libsecret.doap'),
    P(['Gdk', 'GdkX11', 'Gtk'], 'https://git.gnome.org/browse/gtk+/plain/gtk+.doap'),
    P(['ColorHug', 'Colord', 'ColordGtk'], 'https://raw.github.com/hughsie/colord/master/colord.doap'),
    P(['Gsf'], 'https://git.gnome.org/browse/libgsf/plain/libgsf.doap'),
    P(['Gee'], 'https://git.gnome.org/browse/libgee/plain/libgee.doap'),
    P(['LibvirtGConfig', 'LibvirtGLib', 'LibvirtGObject'], 'https://git.gnome.org/browse/libgovirt/plain/libgovirt.doap'),
    P(['EBook', 'EBookContacts', 'EDataServer'], 'https://git.gnome.org/browse/evolution-data-server/plain/evolution-data-server.doap'),
    P(['Gdm'], 'https://git.gnome.org/browse/gdm/plain/gdm.doap'),
    P(['Zpj'], 'https://git.gnome.org/browse/libzapojit/plain/libzapojit.doap'),
    P(['Atspi'], 'https://git.gnome.org/browse/at-spi2-core/plain/at-spi2-core.doap'),
    P(['Gst', 'GstBase', 'GstCheck', 'GstController', 'GstNet'], 'http://cgit.freedesktop.org/gstreamer/gstreamer/plain/gstreamer.doap'),
    P(['Gdl'], 'https://git.gnome.org/browse/gdl/plain/gdl.doap'),
    P(['Anjuta'], 'https://git.gnome.org/browse/anjuta/plain/anjuta.doap'),
    P(['TotemPlParser'], 'https://git.gnome.org/browse/totem-pl-parser/plain/totem-pl-parser.doap'),
    P(['Caribou'], 'https://git.gnome.org/browse/caribou/plain/caribou.doap'),
    P(['ClutterGst'], 'https://git.gnome.org/browse/clutter-gst/plain/clutter-gst.doap'),
    P(['GrlPls'], 'https://git.gnome.org/browse/grilo-plugins/plain/grilo-plugins.doap'),
    P(['GstGL', 'GstInsertBin', 'GstMpegts'], 'http://cgit.freedesktop.org/gstreamer/gst-plugins-bad/plain/gst-plugins-bad.doap'),
    P(['Nautilus'], 'https://git.gnome.org/browse/nautilus/plain/nautilus.doap'),
    P(['GData'], 'https://git.gnome.org/browse/libgdata/plain/libgdata.doap'),
    P(['Folks', 'FolksEds', 'FolksTelepathy'], 'https://git.gnome.org/browse/folks/plain/folks.doap'),
    P(['Gucharmap'], 'https://git.gnome.org/browse/gucharmap/plain/gucharmap.doap'),
    P(['GdkPixbuf'], 'https://git.gnome.org/browse/gdk-pixbuf/plain/gdk-pixbuf.doap'),
    P(['GUPnPAV'], 'https://git.gnome.org/browse/gupnp-av/plain/gupnp-av.doap'),
    P(['BraseroBurn', 'BraseroMedia'], 'https://git.gnome.org/browse/brasero/plain/brasero.doap'),
    P(['GES'], 'http://cgit.freedesktop.org/gstreamer/gst-editing-services/plain/gst-editing-services.doap'),
    P(['GWeather'], 'https://git.gnome.org/browse/libgweather/plain/libgweather.doap'),
    P(['GCab'], 'https://git.gnome.org/browse/gcab/plain/gcab.doap'),
    P(['GXPS'], 'https://git.gnome.org/browse/libgxps/plain/libgxps.doap'),
    P(['Cally', 'Clutter', 'ClutterGdk', 'ClutterX11'], 'https://git.gnome.org/browse/clutter/plain/clutter.doap'),
    P(['GeocodeGlib'], 'https://git.gnome.org/browse/geocode-glib/plain/geocode-glib.doap'),
    P(['Wnck'], 'https://git.gnome.org/browse/libwnck/plain/libwnck.doap'),
    P(['Totem'], 'https://git.gnome.org/browse/totem/plain/totem.doap'),
    P(['GnomeBluetooth'], 'https://git.gnome.org/browse/gnome-bluetooth/plain/gnome-bluetooth.doap'),
    P(['Gdict'], 'https://git.gnome.org/browse/gnome-dictionary/plain/gnome-dictionary.doap'),
    P(['GUPnPDLNA', 'GUPnPDLNAGst'], 'https://git.gnome.org/browse/gupnp-dlna/plain/gupnp-dlna.doap'),
    P(['Vte'], 'https://git.gnome.org/browse/vte/plain/vte.doap'),
    P(['Cogl', 'CoglGst', 'CoglPango'], 'https://git.gnome.org/browse/cogl/plain/cogl.doap'),
    P(['Tracker', 'TrackerControl', 'TrackerExtract', 'TrackerMiner'], 'https://git.gnome.org/browse/tracker/plain/tracker.doap'),
    P(['GLib', 'GObject', 'Gio', 'GModule'], 'https://git.gnome.org/browse/glib/plain/glib.doap'),
    P(['MediaArt'], 'https://git.gnome.org/browse/libmediaart/plain/libmediaart.doap'),
    P(['HarfBuzz'], 'http://cgit.freedesktop.org/harfbuzz/plain/harfbuzz.doap'),
    P(['Gom'], 'https://git.gnome.org/browse/gom/plain/gom.doap'),
    P(['Gnm'], 'https://git.gnome.org/browse/gnumeric/plain/gnumeric.doap'),
]


def get_project(namespace):
    for p in PROJECTS:
        if namespace in p.namespaces:
            return p
    raise KeyError


def get_tag(namespace, project_version):

    def matches(ns):
        return namespace == ns or namespace in get_related_namespaces(ns)

    if matches("Atk"):
        return "ATK_" + project_version.replace(".", "_")
    elif matches("Gtk") or matches("GLib") or matches("Pango"):
        return project_version
    else:
        return ""


def get_source_to_url_func(namespace, project_version):
    """Returns a function for mapping the line number paths to web links
    or None.
    """

    try:
        project = get_project(namespace)
    except KeyError:
        return

    tag = get_tag(namespace, project_version)

    if "git.gnome.org" not in project.doap or not tag:
        return None

    match = re.search("/browse/(.*?)/", project.doap)
    if match is None:
        return
    git_name = match.group(1)

    def gnome_func(path):
        path, line = path.rsplit(":", 1)
        return "https://git.gnome.org/browse/%s/tree/%s?h=%s#n%s" % (
            git_name, path, tag, line)

    return gnome_func


def get_related_namespaces(ns):
    """Returns a list of related namespaces which are part of the
    same project.
    """

    try:
        p = get_project(ns)
    except KeyError:
        return []
    else:
        l = p.namespaces[:]
        l.remove(ns)
        return l
