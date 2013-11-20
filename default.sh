#!/bin/sh

# this is the default build that gets published online

# This list is generated running the below command with "--debian"
#
# sudo apt-get install gir1.2-fcitx-1.0 gsettings-desktop-schemas-dev 
# libatk1.0-dev libcogl-dev libcogl-pango-dev libgdk-pixbuf2.0-dev 
# libgirepository1.0-dev libgrilo-0.2-dev libgstreamer-plugins-base1.0-dev 
# libgstreamer1.0-dev libgtk-3-dev libjson-glib-dev libpango1.0-dev 
# libsoup2.4-dev

./docgen.py -t Atk-1.0 Cogl-1.0 CoglPango-1.0 DBus-1.0 DBusGLib-1.0 \
    Fcitx-1.0 GDesktopEnums-3.0 GIRepository-2.0 GL-1.0 GLib-2.0 GModule-2.0 \
    GObject-2.0 Gdk-3.0 GdkPixbuf-2.0 GdkX11-3.0 Gio-2.0 \
    Grl-0.2 GrlNet-0.2 Gst-1.0 GstAllocators-1.0 GstApp-1.0 GstAudio-1.0 \
    GstBase-1.0 GstCheck-1.0 GstController-1.0 GstFft-1.0 GstNet-1.0 \
    GstPbutils-1.0 GstRiff-1.0 GstRtp-1.0 GstRtsp-1.0 GstSdp-1.0 GstTag-1.0 \
    GstVideo-1.0 Gtk-3.0 Json-1.0 Pango-1.0 PangoCairo-1.0 \
    PangoFT2-1.0 PangoXft-1.0 Soup-2.4 cairo-1.0 fontconfig-2.0 \
    freetype2-2.0 libxml2-2.0 xfixes-4.0 xft-2.0 xlib-2.0 xrandr-1.3 \

./docbuild.py
