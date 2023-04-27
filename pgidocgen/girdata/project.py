# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re
from urllib.parse import quote

from .. import util
from .library import Library
from .util import load_debian


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
        version_strings = []
        for namespace in self.namespaces:
            try:
                rmod = util.import_namespace(namespace, ignore_version=True)
            except ImportError:
                continue
            l = Library.for_namespace(namespace, util.get_module_version(rmod))
            version_strings.append(l.namespace)
            version = l.version
            if version:
                break

        # get the debian package version if all else fails
        if not version:
            debian_info = load_debian()
            for v in version_strings:
                if v in debian_info:
                    version = debian_info[v]["version"]
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
        elif matches("UDisks"):
            # XXX: I don't understand the tagging system they use.. anyone?
            return "udisks-2.6.4"

    def get_source_func(self, namespace, project_version=None):
        """Returns a function for mapping the line number paths to web links
        or None.
        """

        assert namespace in self.namespaces

        version = project_version or self.version
        tag = self.get_tag(version)

        if not tag:
            return None

        if "gitlab.gnome.org" in self.doap:
            match = re.search("/GNOME/(.*?)/", self.doap)
            if match is None:
                return
            git_name = match.group(1)

            def gnome_func(path):
                path, line = path.rsplit(":", 1)
                return "https://gitlab.gnome.org/GNOME/%s/blob/%s/%s#L%s" % (
                    git_name, tag, path, line)

            return gnome_func
        elif "gitlab.freedesktop.org/gstreamer/" in self.doap:
            match = re.search("/gstreamer/(.*?)/", self.doap)
            if match is None:
                return
            git_name = match.group(1)

            path_prefix = ""
            if "Gst" in self.namespaces and namespace != "Gst":
                path_prefix = "libs/gst/"

            def gst_func(path):
                path, line = path.rsplit(":", 1)
                return ("https://gitlab.freedesktop.org/gstreamer/%s/blob/%s/%s%s"
                        "#L%s" % (git_name, tag, path_prefix, path, line))

            return gst_func
        elif namespace in ("AppStreamGlib",):

            def func(path):
                path, line = path.rsplit(":", 1)
                return "https://github.com/hughsie/appstream-glib/tree/%s/%s#L%s" % (tag, path, line)

            return func
        elif namespace in ("Cattle",):

            def func(path):
                path, line = path.rsplit(":", 1)
                return "http://git.kiyuko.org/cgi-bin/browse?p=cattle;a=blob;f=%s;hb=%s#l%s" % (quote(path), tag, line)

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
        elif namespace in ("UDisks",):

            def func(path):
                path, line = path.rsplit(":", 1)
                return "https://github.com/storaged-project/udisks/blob/%s/%s#L%s" % (tag, path, line)

            return func


PROJECTS = [
    Project(['Goa'], 'https://gitlab.gnome.org/GNOME/gnome-online-accounts/raw/master/gnome-online-accounts.doap'),
    Project(['GnomeDesktop'], 'https://gitlab.gnome.org/GNOME/gnome-desktop/raw/master/gnome-desktop.doap'),
    Project(['Gladeui'], 'https://gitlab.gnome.org/GNOME/glade/raw/master/glade.doap'),
    Project(['GVnc', 'GVncPulse', 'GtkVnc'], 'https://gitlab.gnome.org/GNOME/gtk-vnc/raw/master/gtk-vnc.doap'),
    Project(['Peas', 'PeasGtk'], 'https://gitlab.gnome.org/GNOME/libpeas/raw/main/libpeas.doap'),
    Project(['CryptUI'], 'https://gitlab.gnome.org/GNOME/libcryptui/raw/master/libcryptui.doap'),
    Project(['DBus', 'DBusGLib', 'GIRepository', 'GL', 'cairo', 'fontconfig', 'freetype2', 'libxml2', 'win32', 'xfixes', 'xft', 'xlib', 'xrandr'], 'https://gitlab.gnome.org/GNOME/gobject-introspection/raw/main/gobject-introspection.doap'),
    Project(['EvinceDocument', 'EvinceView'], 'https://gitlab.gnome.org/GNOME/evince/raw/main/evince.doap'),
    Project(['PackageKitGlib', 'PackageKitPlugin'], 'https://raw.githubusercontent.com/hughsie/PackageKit/master/PackageKit.doap'),
    Project(['Gkbd'], 'https://gitlab.gnome.org/GNOME/libgnomekbd/raw/master/libgnomekbd.doap'),
    Project(['GtkClutter'], 'https://gitlab.gnome.org/GNOME/clutter-gtk/raw/master/clutter-gtk.doap'),
    Project(['GDesktopEnums'], 'https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/raw/master/gsettings-desktop-schemas.doap'),
    Project(['GExiv2'], 'https://gitlab.gnome.org/GNOME/gexiv2/raw/master/gexiv2.doap'),
    Project(['Rsvg'], 'https://gitlab.gnome.org/GNOME/librsvg/raw/main/librsvg.doap'),
    Project(['GnomeKeyring'], 'https://gitlab.gnome.org/GNOME/gnome-keyring/raw/master/gnome-keyring.doap'),
    Project(['Atk'], 'https://gitlab.gnome.org/GNOME/atk/raw/master/atk.doap'),
    Project(['GtkSource'], 'https://gitlab.gnome.org/GNOME/gtksourceview/raw/master/gtksourceview.doap'),
    Project(['GTop'], 'https://gitlab.gnome.org/GNOME/libgtop/raw/master/libgtop.doap'),
    Project(['Rest', 'RestExtras'], 'https://gitlab.gnome.org/GNOME/librest/raw/master/librest.doap'),
    Project(['Gck', 'Gcr', 'GcrUi'], 'https://gitlab.gnome.org/GNOME/gcr/raw/master/gcr.doap'),
    Project(['Notify'], 'https://gitlab.gnome.org/GNOME/libnotify/raw/master/libnotify.doap'),
    Project(['GUPnPIgd'], 'https://gitlab.gnome.org/GNOME/gupnp-igd/raw/master/gupnp-igd.doap'),
    Project(['SocialWebClient'], 'https://gitlab.gnome.org/Archive/libsocialweb/raw/master/libsocialweb.doap'),
    Project(['PanelApplet'], 'https://gitlab.gnome.org/GNOME/gnome-panel/raw/master/gnome-panel.doap'),
    Project(['GUPnP'], 'https://gitlab.gnome.org/GNOME/gupnp/raw/master/gupnp.doap'),
    Project(['GSSDP'], 'https://gitlab.gnome.org/GNOME/gssdp/raw/master/gssdp.doap'),
    Project(['GOffice'], 'https://gitlab.gnome.org/GNOME/goffice/raw/master/goffice.doap'),
    Project(['Cheese'], 'https://gitlab.gnome.org/GNOME/cheese/raw/master/cheese.doap'),
    Project(['Pango', 'PangoCairo', 'PangoFT2', 'PangoXft'], 'https://gitlab.gnome.org/GNOME/pango/raw/main/pango.doap'),
    Project(['Gda'], 'https://gitlab.gnome.org/GNOME/libgda/raw/master/libgda.doap'),
    Project(['GConf'], 'https://gitlab.gnome.org/Archive/gconf/raw/master/gconf.doap'),
    Project(['Soup', 'SoupGNOME'], 'https://gitlab.gnome.org/GNOME/libsoup/raw/master/libsoup.doap'),
    Project(['MPID', 'RB'], 'https://gitlab.gnome.org/GNOME/rhythmbox/raw/master/rhythmbox.doap'),
    Project(['Gegl'], 'https://gitlab.gnome.org/GNOME/gegl/raw/master/gegl.doap'),
    Project(['Grl', 'GrlNet'], 'https://gitlab.gnome.org/GNOME/grilo/raw/master/grilo.doap'),
    Project(['GMenu'], 'https://gitlab.gnome.org/GNOME/gnome-menus/raw/master/gnome-menus.doap'),
    Project(['Json'], 'https://gitlab.gnome.org/GNOME/json-glib/raw/master/json-glib.doap'),
    Project(['GstAllocators', 'GstApp', 'GstAudio', 'GstInterfaces', 'GstNetbuffer', 'GstPbutils', 'GstRiff', 'GstRtp', 'GstRtsp', 'GstSdp', 'GstTag', 'GstVideo'], 'https://gitlab.freedesktop.org/gstreamer/gst-plugins-base/raw/master/gst-plugins-base.doap'),
    Project(['GstRtspServer'], 'https://gitlab.freedesktop.org/gstreamer/gst-rtsp-server/raw/master/gst-rtsp-server.doap'),
    Project(['GUdev'], 'https://gitlab.gnome.org/GNOME/libgudev/raw/master/libgudev.doap'),
    Project(['Champlain', 'GtkChamplain'], 'https://gitlab.gnome.org/GNOME/libchamplain/raw/master/libchamplain.doap'),
    Project(['Secret', 'SecretUnstable'], 'https://gitlab.gnome.org/GNOME/libsecret/raw/master/libsecret.doap'),
    Project(['Gdk', 'GdkX11', 'Gtk'], 'https://gitlab.gnome.org/GNOME/gtk/raw/main/gtk.doap'),
    Project(['ColorHug', 'Colord'], 'https://raw.github.com/hughsie/colord/master/colord.doap'),
    Project(['ColordGtk'], 'https://raw.github.com/hughsie/colord-gtk/master/colord-gtk.doap'),
    Project(['Gsf'], 'https://gitlab.gnome.org/GNOME/libgsf/raw/master/libgsf.doap'),
    Project(['LibvirtGConfig', 'LibvirtGLib', 'LibvirtGObject'], 'https://gitlab.gnome.org/GNOME/libgovirt/raw/master/libgovirt.doap'),
    Project(['EBook', 'EBookContacts', 'EDataServer'], 'https://gitlab.gnome.org/GNOME/evolution-data-server/raw/master/evolution-data-server.doap'),
    Project(['Gdm'], 'https://gitlab.gnome.org/GNOME/gdm/raw/main/gdm.doap'),
    Project(['Zpj'], 'https://gitlab.gnome.org/GNOME/libzapojit/raw/master/libzapojit.doap'),
    Project(['Atspi'], 'https://gitlab.gnome.org/GNOME/at-spi2-core/raw/main/at-spi2-core.doap'),
    Project(['Gst', 'GstBase', 'GstCheck', 'GstController', 'GstNet'], 'https://gitlab.freedesktop.org/gstreamer/gstreamer/raw/master/gstreamer.doap'),
    Project(['Gdl'], 'https://gitlab.gnome.org/GNOME/gdl/raw/master/gdl.doap'),
    Project(['Anjuta'], 'https://gitlab.gnome.org/GNOME/anjuta/raw/master/anjuta.doap'),
    Project(['TotemPlParser'], 'https://gitlab.gnome.org/GNOME/totem-pl-parser/raw/master/totem-pl-parser.doap'),
    Project(['Caribou'], 'https://gitlab.gnome.org/GNOME/caribou/raw/master/caribou.doap'),
    Project(['ClutterGst'], 'https://gitlab.gnome.org/GNOME/clutter-gst/raw/master/clutter-gst.doap'),
    Project(['GrlPls'], 'https://gitlab.gnome.org/GNOME/grilo-plugins/raw/master/grilo-plugins.doap'),
    Project(['GstGL', 'GstInsertBin', 'GstMpegts'], 'https://gitlab.freedesktop.org/gstreamer/gst-plugins-bad/raw/master/gst-plugins-bad.doap'),
    Project(['Nautilus'], 'https://gitlab.gnome.org/GNOME/nautilus/raw/main/nautilus.doap'),
    Project(['GData'], 'https://gitlab.gnome.org/GNOME/libgdata/raw/main/libgdata.doap'),
    Project(['Folks', 'FolksEds', 'FolksTelepathy'], 'https://gitlab.gnome.org/GNOME/folks/raw/master/folks.doap'),
    Project(['Gucharmap'], 'https://gitlab.gnome.org/GNOME/gucharmap/raw/master/gucharmap.doap'),
    Project(['GdkPixbuf', 'GdkPixdata'], 'https://gitlab.gnome.org/GNOME/gdk-pixbuf/raw/master/gdk-pixbuf.doap'),
    Project(['GUPnPAV'], 'https://gitlab.gnome.org/GNOME/gupnp-av/raw/master/gupnp-av.doap'),
    Project(['BraseroBurn', 'BraseroMedia'], 'https://gitlab.gnome.org/GNOME/brasero/raw/master/brasero.doap'),
    Project(['GES'], 'https://gitlab.freedesktop.org/gstreamer/gst-editing-services/raw/master/gst-editing-services.doap'),
    Project(['GWeather'], 'https://gitlab.gnome.org/GNOME/libgweather/raw/main/libgweather.doap'),
    Project(['GCab'], 'https://gitlab.gnome.org/GNOME/gcab/raw/master/gcab.doap'),
    Project(['GXPS'], 'https://gitlab.gnome.org/GNOME/libgxps/raw/master/libgxps.doap'),
    Project(['Cally', 'Clutter', 'ClutterGdk', 'ClutterX11'], 'https://gitlab.gnome.org/GNOME/clutter/raw/master/clutter.doap'),
    Project(['GeocodeGlib'], 'https://gitlab.gnome.org/GNOME/geocode-glib/raw/master/geocode-glib.doap'),
    Project(['Wnck'], 'https://gitlab.gnome.org/GNOME/libwnck/raw/master/libwnck.doap'),
    Project(['Totem'], 'https://gitlab.gnome.org/GNOME/totem/raw/master/totem.doap'),
    Project(['GnomeBluetooth'], 'https://gitlab.gnome.org/GNOME/gnome-bluetooth/raw/master/gnome-bluetooth.doap'),
    Project(['Gdict'], 'https://gitlab.gnome.org/GNOME/gnome-dictionary/raw/master/gnome-dictionary.doap'),
    Project(['GUPnPDLNA', 'GUPnPDLNAGst'], 'https://gitlab.gnome.org/GNOME/gupnp-dlna/raw/master/gupnp-dlna.doap'),
    Project(['Vte'], 'https://gitlab.gnome.org/GNOME/vte/raw/master/vte.doap'),
    Project(['Cogl', 'CoglGst', 'CoglPango'], 'https://gitlab.gnome.org/GNOME/cogl/raw/master/cogl.doap'),
    Project(['Tracker', 'TrackerControl', 'TrackerExtract', 'TrackerMiner'], 'https://gitlab.gnome.org/GNOME/tracker/raw/master/tracker.doap'),
    Project(['GLib', 'GObject', 'Gio', 'GModule'], 'https://gitlab.gnome.org/GNOME/glib/raw/main/glib.doap'),
    Project(['MediaArt'], 'https://gitlab.gnome.org/GNOME/libmediaart/raw/master/libmediaart.doap'),
    Project(['HarfBuzz'], 'https://raw.githubusercontent.com/harfbuzz/harfbuzz/master/harfbuzz.doap'),
    Project(['Gom'], 'https://gitlab.gnome.org/GNOME/gom/raw/master/gom.doap'),
    Project(['Gnm'], 'https://gitlab.gnome.org/GNOME/gnumeric/raw/master/gnumeric.doap'),
    Project(['UDisks']),
    Project(['Dazzle'], 'https://gitlab.gnome.org/GNOME/libdazzle/raw/master/libdazzle.doap'),
]
