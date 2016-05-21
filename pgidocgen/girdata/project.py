# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re
import urllib

from .. import util
from .library import Library


class Project(object):
    """A project is roughly something which gets released at the same time and
    has the same release version number. In most cases one git repo. The
    namespaces might not actually be included in the project but the libraries
    of the GIR are (e.g. GLib-2.0.gir is in libgirepository, but it's part of
    GLib)
    """

    def __init__(self, namespaces, doap=None):
        self.namespaces = namespaces
        self.doap = doap or ""

    @classmethod
    def for_namespace(cls, namespace):
        """Returns a Project instance for a given namespace"""

        for p in PROJECTS:
            if namespace in p.namespaces:
                return p
        return Project([namespace])

    @util.cached_property
    def version(self):
        """Returns the version of the current module or some related module in
        the same project, or an empty string
        """

        version = ""
        for namespace in self.namespaces:
            try:
                rmod = util.import_namespace(namespace, ignore_version=True)
            except ImportError:
                continue
            l = Library.for_namespace(namespace, util.get_module_version(rmod))
            version = l.version
            if version:
                break

        return version

    def get_tag(self, project_version=None):
        """Returns the VCS tag for the given `namespace` and the library
        version like Project.version.

        In case not tag can be found returns an empty string.
        """

        version = project_version or self.version
        if not version:
            return ""

        def matches(ns):
            return ns in self.namespaces

        if matches("Atk"):
            return "ATK_" + version.replace(".", "_")
        elif matches("Gtk") or matches("GLib") or matches("Pango") or \
                matches("GdkPixbuf") or matches("Colord") or \
                matches("Gck") or matches("Fwupd"):
            return version
        elif "/gstreamer/" in self.doap:
            return ".".join(version.split(".")[:3])
        elif matches("AppStreamGlib"):
            return "appstream_glib_" + version.replace(".", "_")
        elif matches("Cattle"):
            return "cattle-" + version
        elif matches("GExiv2"):
            return "gexiv2-" + version
        elif matches("Anthy"):
            return "release/" + version

    def get_source_func(self, namespace, project_version=None):
        """Returns a function for mapping the line number paths to web links
        or None.
        """

        assert namespace in self.namespaces

        version = project_version or self.version
        tag = self.get_tag(self.version)

        if not tag:
            return None

        if "git.gnome.org" in self.doap:
            match = re.search("/browse/(.*?)/", self.doap)
            if match is None:
                return
            git_name = match.group(1)

            def gnome_func(path):
                path, line = path.rsplit(":", 1)
                return "https://git.gnome.org/browse/%s/tree/%s?h=%s#n%s" % (
                    git_name, path, tag, line)

            return gnome_func
        elif "cgit.freedesktop.org/gstreamer/" in self.doap:
            match = re.search("/gstreamer/(.*?)/", self.doap)
            if match is None:
                return
            git_name = match.group(1)

            path_prefix = ""
            if namespace.startswith("Gst") and \
                    "/gst-plugins-base/" in self.doap:
                path_prefix = "gst-libs/gst/"
            elif "Gst" in self.namespaces and namespace != "Gst":
                path_prefix = "libs/gst/"

            def gst_func(path):
                path, line = path.rsplit(":", 1)
                return ("http://cgit.freedesktop.org/gstreamer/%s/tree/%s%s"
                        "?h=%s#n%s" % (git_name, path_prefix, path, tag, line))

            return gst_func
        elif namespace in ("AppStreamGlib",):

            def func(path):
                path, line = path.rsplit(":", 1)
                return "https://github.com/hughsie/appstream-glib/tree/%s/%s#L%s" % (tag, path, line)

            return func
        elif namespace in ("Cattle",):

            def func(path):
                path, line = path.rsplit(":", 1)
                return "http://git.kiyuko.org/cgi-bin/browse?p=cattle;a=blob;f=%s;hb=%s#l%s" % (urllib.quote(path), tag, line)

            return func
        elif namespace in ("Colord", "ColorHug"):

            def func(path):
                path, line = path.rsplit(":", 1)
                return "https://github.com/hughsie/colord/blob/%s/lib/%s#L%s" % (tag, path, line)

            return func
        elif namespace in ("Fwupd",):

            def func(path):
                path, line = path.rsplit(":", 1)
                return "https://github.com/hughsie/fwupd/blob/%s/%s#L%s" % (tag, path, line)

            return func
        elif namespace in ("Anthy",):

            def func(path):
                path, line = path.rsplit(":", 1)
                return "https://anonscm.debian.org/cgit/collab-maint/anthy.git/tree/%s?h=%s#n%s" % (path, tag, line)

            return func


PROJECTS = [
    Project(['Goa'], 'https://git.gnome.org/browse/gnome-online-accounts/plain/gnome-online-accounts.doap'),
    Project(['GnomeDesktop'], 'https://git.gnome.org/browse/gnome-desktop/plain/gnome-desktop.doap'),
    Project(['Gladeui'], 'https://git.gnome.org/browse/glade/plain/glade.doap'),
    Project(['GVnc', 'GVncPulse', 'GtkVnc'], 'https://git.gnome.org/browse/gtk-vnc/plain/gtk-vnc.doap'),
    Project(['Peas', 'PeasGtk'], 'https://git.gnome.org/browse/libpeas/plain/libpeas.doap'),
    Project(['CryptUI'], 'https://git.gnome.org/browse/libcryptui/plain/libcryptui.doap'),
    Project(['DBus', 'DBusGLib', 'GIRepository', 'GL', 'cairo', 'fontconfig', 'freetype2', 'libxml2', 'win32', 'xfixes', 'xft', 'xlib', 'xrandr'], 'https://git.gnome.org/browse/gobject-introspection/plain/gobject-introspection.doap'),
    Project(['EvinceDocument', 'EvinceView'], 'https://git.gnome.org/browse/evince/plain/evince.doap'),
    Project(['PackageKitGlib', 'PackageKitPlugin'], 'https://raw.githubusercontent.com/hughsie/PackageKit/master/PackageKit.doap'),
    Project(['Gkbd'], 'https://git.gnome.org/browse/libgnomekbd/plain/libgnomekbd.doap'),
    Project(['GtkClutter'], 'https://git.gnome.org/browse/clutter-gtk/plain/clutter-gtk.doap'),
    Project(['GDesktopEnums'], 'https://git.gnome.org/browse/gsettings-desktop-schemas/plain/gsettings-desktop-schemas.doap'),
    Project(['GExiv2'], 'https://git.gnome.org/browse/gexiv2/plain/gexiv2.doap'),
    Project(['Rsvg'], 'https://git.gnome.org/browse/librsvg/plain/librsvg.doap'),
    Project(['GnomeKeyring'], 'https://git.gnome.org/browse/gnome-keyring/plain/gnome-keyring.doap'),
    Project(['Atk'], 'https://git.gnome.org/browse/atk/plain/atk.doap'),
    Project(['GtkSource'], 'https://git.gnome.org/browse/gtksourceview/plain/gtksourceview.doap'),
    Project(['GTop'], 'https://git.gnome.org/browse/libgtop/plain/libgtop.doap'),
    Project(['Rest', 'RestExtras'], 'https://git.gnome.org/browse/librest/plain/librest.doap'),
    Project(['Gck', 'Gcr', 'GcrUi'], 'https://git.gnome.org/browse/gcr/plain/gcr.doap'),
    Project(['Notify'], 'https://git.gnome.org/browse/libnotify/plain/libnotify.doap'),
    Project(['GUPnPIgd'], 'https://git.gnome.org/browse/gupnp-igd/plain/gupnp-igd.doap'),
    Project(['SocialWebClient'], 'https://git.gnome.org/browse/libsocialweb/plain/libsocialweb.doap'),
    Project(['PanelApplet'], 'https://git.gnome.org/browse/gnome-panel/plain/gnome-panel.doap'),
    Project(['GUPnP'], 'https://git.gnome.org/browse/gupnp/plain/gupnp.doap'),
    Project(['GSSDP'], 'https://git.gnome.org/browse/gssdp/plain/gssdp.doap'),
    Project(['GOffice'], 'https://git.gnome.org/browse/goffice/plain/goffice.doap'),
    Project(['Cheese'], 'https://git.gnome.org/browse/cheese/plain/cheese.doap'),
    Project(['Pango', 'PangoCairo', 'PangoFT2', 'PangoXft'], 'https://git.gnome.org/browse/pango/plain/pango.doap'),
    Project(['Gda'], 'https://git.gnome.org/browse/libgda/plain/libgda.doap'),
    Project(['GConf'], 'https://git.gnome.org/browse/gconf/plain/gconf.doap'),
    Project(['Soup', 'SoupGNOME'], 'https://git.gnome.org/browse/libsoup/plain/libsoup.doap'),
    Project(['MPID', 'RB'], 'https://git.gnome.org/browse/rhythmbox/plain/rhythmbox.doap'),
    Project(['Gegl'], 'https://git.gnome.org/browse/gegl/plain/gegl.doap'),
    Project(['Grl', 'GrlNet'], 'https://git.gnome.org/browse/grilo/plain/grilo.doap'),
    Project(['GMenu'], 'https://git.gnome.org/browse/gnome-menus/plain/gnome-menus.doap'),
    Project(['Json'], 'https://git.gnome.org/browse/json-glib/plain/json-glib.doap'),
    Project(['GstAllocators', 'GstApp', 'GstAudio', 'GstFft', 'GstInterfaces', 'GstNetbuffer', 'GstPbutils', 'GstRiff', 'GstRtp', 'GstRtsp', 'GstSdp', 'GstTag', 'GstVideo'], 'http://cgit.freedesktop.org/gstreamer/gst-plugins-base/plain/gst-plugins-base.doap'),
    Project(['GstRtspServer'], 'http://cgit.freedesktop.org/gstreamer/gst-rtsp-server/plain/gst-rtsp-server.doap'),
    Project(['GUdev'], 'https://git.gnome.org/browse/libgudev/plain/libgudev.doap'),
    Project(['Champlain', 'GtkChamplain'], 'https://git.gnome.org/browse/libchamplain/plain/libchamplain.doap'),
    Project(['Secret', 'SecretUnstable'], 'https://git.gnome.org/browse/libsecret/plain/libsecret.doap'),
    Project(['Gdk', 'GdkX11', 'Gtk'], 'https://git.gnome.org/browse/gtk+/plain/gtk+.doap'),
    Project(['ColorHug', 'Colord'], 'https://raw.github.com/hughsie/colord/master/colord.doap'),
    Project(['ColordGtk'], 'https://github.com/hughsie/colord-gtk/blob/master/colord-gtk.doap'),
    Project(['Gsf'], 'https://git.gnome.org/browse/libgsf/plain/libgsf.doap'),
    Project(['Gee'], 'https://git.gnome.org/browse/libgee/plain/libgee.doap'),
    Project(['LibvirtGConfig', 'LibvirtGLib', 'LibvirtGObject'], 'https://git.gnome.org/browse/libgovirt/plain/libgovirt.doap'),
    Project(['EBook', 'EBookContacts', 'EDataServer'], 'https://git.gnome.org/browse/evolution-data-server/plain/evolution-data-server.doap'),
    Project(['Gdm'], 'https://git.gnome.org/browse/gdm/plain/gdm.doap'),
    Project(['Zpj'], 'https://git.gnome.org/browse/libzapojit/plain/libzapojit.doap'),
    Project(['Atspi'], 'https://git.gnome.org/browse/at-spi2-core/plain/at-spi2-core.doap'),
    Project(['Gst', 'GstBase', 'GstCheck', 'GstController', 'GstNet'], 'http://cgit.freedesktop.org/gstreamer/gstreamer/plain/gstreamer.doap'),
    Project(['Gdl'], 'https://git.gnome.org/browse/gdl/plain/gdl.doap'),
    Project(['Anjuta'], 'https://git.gnome.org/browse/anjuta/plain/anjuta.doap'),
    Project(['TotemPlParser'], 'https://git.gnome.org/browse/totem-pl-parser/plain/totem-pl-parser.doap'),
    Project(['Caribou'], 'https://git.gnome.org/browse/caribou/plain/caribou.doap'),
    Project(['ClutterGst'], 'https://git.gnome.org/browse/clutter-gst/plain/clutter-gst.doap'),
    Project(['GrlPls'], 'https://git.gnome.org/browse/grilo-plugins/plain/grilo-plugins.doap'),
    Project(['GstGL', 'GstInsertBin', 'GstMpegts'], 'http://cgit.freedesktop.org/gstreamer/gst-plugins-bad/plain/gst-plugins-bad.doap'),
    Project(['Nautilus'], 'https://git.gnome.org/browse/nautilus/plain/nautilus.doap'),
    Project(['GData'], 'https://git.gnome.org/browse/libgdata/plain/libgdata.doap'),
    Project(['Folks', 'FolksEds', 'FolksTelepathy'], 'https://git.gnome.org/browse/folks/plain/folks.doap'),
    Project(['Gucharmap'], 'https://git.gnome.org/browse/gucharmap/plain/gucharmap.doap'),
    Project(['GdkPixbuf'], 'https://git.gnome.org/browse/gdk-pixbuf/plain/gdk-pixbuf.doap'),
    Project(['GUPnPAV'], 'https://git.gnome.org/browse/gupnp-av/plain/gupnp-av.doap'),
    Project(['BraseroBurn', 'BraseroMedia'], 'https://git.gnome.org/browse/brasero/plain/brasero.doap'),
    Project(['GES'], 'http://cgit.freedesktop.org/gstreamer/gst-editing-services/plain/gst-editing-services.doap'),
    Project(['GWeather'], 'https://git.gnome.org/browse/libgweather/plain/libgweather.doap'),
    Project(['GCab'], 'https://git.gnome.org/browse/gcab/plain/gcab.doap'),
    Project(['GXPS'], 'https://git.gnome.org/browse/libgxps/plain/libgxps.doap'),
    Project(['Cally', 'Clutter', 'ClutterGdk', 'ClutterX11'], 'https://git.gnome.org/browse/clutter/plain/clutter.doap'),
    Project(['GeocodeGlib'], 'https://git.gnome.org/browse/geocode-glib/plain/geocode-glib.doap'),
    Project(['Wnck'], 'https://git.gnome.org/browse/libwnck/plain/libwnck.doap'),
    Project(['Totem'], 'https://git.gnome.org/browse/totem/plain/totem.doap'),
    Project(['GnomeBluetooth'], 'https://git.gnome.org/browse/gnome-bluetooth/plain/gnome-bluetooth.doap'),
    Project(['Gdict'], 'https://git.gnome.org/browse/gnome-dictionary/plain/gnome-dictionary.doap'),
    Project(['GUPnPDLNA', 'GUPnPDLNAGst'], 'https://git.gnome.org/browse/gupnp-dlna/plain/gupnp-dlna.doap'),
    Project(['Vte'], 'https://git.gnome.org/browse/vte/plain/vte.doap'),
    Project(['Cogl', 'CoglGst', 'CoglPango'], 'https://git.gnome.org/browse/cogl/plain/cogl.doap'),
    Project(['Tracker', 'TrackerControl', 'TrackerExtract', 'TrackerMiner'], 'https://git.gnome.org/browse/tracker/plain/tracker.doap'),
    Project(['GLib', 'GObject', 'Gio', 'GModule'], 'https://git.gnome.org/browse/glib/plain/glib.doap'),
    Project(['MediaArt'], 'https://git.gnome.org/browse/libmediaart/plain/libmediaart.doap'),
    Project(['HarfBuzz'], 'http://cgit.freedesktop.org/harfbuzz/plain/harfbuzz.doap'),
    Project(['Gom'], 'https://git.gnome.org/browse/gom/plain/gom.doap'),
    Project(['Gnm'], 'https://git.gnome.org/browse/gnumeric/plain/gnumeric.doap'),
]
