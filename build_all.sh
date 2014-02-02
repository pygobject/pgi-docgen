#!/bin/sh
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# this is the default build that gets published online

./pgi-docgen.py -f _docs Atk-1.0 Cogl-1.0 CoglPango-1.0 DBus-1.0 \
    DBusGLib-1.0 Fcitx-1.0 GDesktopEnums-3.0 GIRepository-2.0 GL-1.0 GLib-2.0 \
    GModule-2.0 GObject-2.0 Gdk-3.0 GdkPixbuf-2.0 GdkX11-3.0 Gio-2.0 \
    Grl-0.2 GrlNet-0.2 Gst-1.0 GstAllocators-1.0 GstApp-1.0 GstAudio-1.0 \
    GstBase-1.0 GstCheck-1.0 GstController-1.0 GstFft-1.0 GstNet-1.0 \
    GstPbutils-1.0 GstRiff-1.0 GstRtp-1.0 GstRtsp-1.0 GstSdp-1.0 GstTag-1.0 \
    GstVideo-1.0 Gtk-3.0 Json-1.0 Pango-1.0 PangoCairo-1.0 Gda-5.0 \
    PangoFT2-1.0 PangoXft-1.0 Soup-2.4 cairo-1.0 fontconfig-2.0 \
    freetype2-2.0 libxml2-2.0 xfixes-4.0 xft-2.0 xlib-2.0 xrandr-1.3 \
    Notify-0.7 Cally-1.0 Clutter-1.0 ClutterGdk-1.0 ClutterX11-1.0 \
    ClutterGst-2.0 JavaScriptCore-3.0 AccountsService-1.0 \
    Anjuta-3.0 Anthy-9000 AppIndicator3-0.1 Atspi-2.0 Gladeui-2.0 \
    Caribou-1.0 Champlain-0.12 Cheese-3.0 Colord-1.0 ColordGtk-1.0 \
    ColorHug-1.0 CryptUI-0.0 Dbusmenu-0.4 DbusmenuGtk3-0.4 Dee-1.0 \
    EBook-1.2 EBookContacts-1.2 EDataServer-1.2 Evd-0.1 EvinceDocument-3.0 \
    EvinceView-3.0 Gck-1 GConf-2.0 Gcr-3 GcrUi-3 GData-0.0 Gdl-3 Gdm-1.0 \
    GeocodeGlib-1.0 GExiv2-0.4 Gkbd-3.0 GMenu-3.0 GnomeBluetooth-1.0 \
    GnomeDesktop-3.0 GnomeKeyring-1.0 Goa-1.0 Gsf-1 Farstream-0.2 \
    GSSDP-1.0 GtkChamplain-0.12 GtkClutter-1.0 GtkSource-3.0 GtkSpell-3.0 \
    GtkVnc-2.0 Gucharmap-2.90 GUdev-1.0 GUPnP-1.0 UDisks-2.0 GUPnPAV-1.0 \
    GUPnPDLNA-2.0 GUPnPDLNAGst-2.0 MPID-3.0 Secret-1  Vte-2.90 \
    GUPnPIgd-1.0 GUsb-1.0 GVnc-1.0 GVncPulse-1.0 GWeather-3.0 GXPS-0.1 \
    IBus-1.0 Indicate-0.7 Itl-1.0 Poppler-0.18 Clinica-0.3 Tracker-0.16 \
    Keybinder-0.0 LangTag-0.5 libisocodes-1.0 Libosinfo-1.0 TrackerMiner-0.16 \
    LibvirtGConfig-1.0 LibvirtGLib-1.0 LibvirtGObject-1.0 TrackerExtract-0.16 \
    LunarDate-2.0 Mx-1.0 Nautilus-3.0 Nemo-3.0 NetworkManager-1.0 \
    PackageKitGlib-1.0 PackageKitPlugin-1.0 PanelApplet-4.0 Gee-0.8 \
    Peas-1.0 PeasGtk-1.0 Polkit-1.0 UPowerGlib-1.0 SecretUnstable-0 \
    PolkitAgent-1.0 Rest-0.7 RestExtras-0.7 Rsvg-2.0 UMockdev-1.0 \
    SocialWebClient-0.25 SoupGNOME-2.4 SpiceClientGLib-2.0 Folks-0.6 \
    SpiceClientGtk-3.0 SugarGestures-1.0 TelepathyGLib-0.12 Wnck-3.0 \
    TelepathyLogger-0.2 TotemPlParser-1.0 Xkl-1.0 Zpj-0.0 Zeitgeist-2.0 \
    && ./pgi-docgen-build.py _docs/_build _docs
