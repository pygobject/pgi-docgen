#!/usr/bin/python
# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import re
import requests
from multiprocessing import Pool

import pgi
pgi.require_version("Gtk", "3.0")

from pgi.repository import Gtk


DESTINATION = os.path.join("data", "clsimages", "Gtk-3.0")

GTK_MAPPING = {
    "Gtk.Button": "button",
    "Gtk.Switch": "switch",
    "Gtk.ToggleButton": "toggle-button",
    "Gtk.CheckButton": "check-button",
    "Gtk.LinkButton": "link-button",
    "Gtk.MenuButton": "menu-button",
    "Gtk.LockButton": "lock-button",
    "Gtk.Entry": "entry",
    "Gtk.SearchEntry": "search-entry",
    "Gtk.RadioButton": "radio-group",
    "Gtk.Label": "label",
    "Gtk.AccelLabel": "accel-label",
    "Gtk.ComboBox": "combo-box",
    "Gtk.ComboBoxText": "combo-box-text",
    "Gtk.InfoBar": "info-bar",
    "Gtk.RecentChooserDialog": "recentchooserdialog",
    "Gtk.TextView": "multiline-text",
    "Gtk.TreeView": "list-and-tree",
    "Gtk.IconView": "icon-view",
    "Gtk.ColorButton": "color-button",
    "Gtk.FontButton": "font-button",
    "Gtk.FileChooserButton": "file-button",
    "Gtk.Separator": "separator",
    "Gtk.Paned": "panes",
    "Gtk.Frame": "frame",
    "Gtk.Window": "window",
    "Gtk.FileChooser": "filechooser",
    "Gtk.PageSetup": "pagesetupdialog",
    "Gtk.Toolbar": "toolbar",
    "Gtk.ToolPalette": "toolpalette",
    "Gtk.MenuBar": "menubar",
    "Gtk.MessageDialog": "messagedialog",
    "Gtk.AboutDialog": "aboutdialog",
    "Gtk.Notebook": "notebook",
    "Gtk.ProgressBar": "progressbar",
    "Gtk.LevelBar": "levelbar",
    "Gtk.ScrolledWindow": "scrolledwindow",
    "Gtk.Scrollbar": "scrollbar",
    "Gtk.SpinButton": "spinbutton",
    "Gtk.Statusbar": "statusbar",
    "Gtk.Scale": "scales",
    "Gtk.Image": "image",
    "Gtk.Spinner": "spinner",
    "Gtk.VolumeButton": "volumebutton",
    "Gtk.Assistant": "assistant",
    "Gtk.AppChooserButton": "appchooserbutton",
    "Gtk.AppChooserDialog": "appchooserdialog",
    "Gtk.FontChooserDialog": "fontchooser",
    "Gtk.ColorChooserDialog": "colorchooser",
    "Gtk.HeaderBar": "headerbar",
    "Gtk.PlacesSidebar": "placessidebar",
    "Gtk.Stack": "stack",
    "Gtk.StackSwitcher": "stackswitcher",
    "Gtk.ListBox": "list-box",
    "Gtk.FlowBox": "flow-box",
    "Gtk.ActionBar": "action-bar",
    "Gtk.ComboBoxText": "combo-box-text",
    "Gtk.PlacesSidebar": "placessidebar",
    "Gtk.SearchBar": "search-bar",
    "Gtk.Frame": "frame",
    "Gtk.Sidebar": "sidebar",
    "Gtk.GLArea": "glarea",
    "Gtk.LockButton": "lockbutton",
}

GTK_URL = ("https://git.gnome.org/browse/gtk+/plain/docs/"
           "reference/gtk/images/%s.png")

MAPPING = dict([(k, GTK_URL  % v) for k, v in GTK_MAPPING.items()])

def fetch(args):
    key, url = args
    print key
    resp = requests.get(url)
    return key, resp.content


def main(dest, mapping):
    # make sure there are no typos in the mapping
    for key in mapping.keys():
        if not hasattr(Gtk, key.split(".")[-1]):
            print key, "missing..."

    missing = []
    for name in dir(Gtk):
        value = getattr(Gtk, name)
        try:
            if issubclass(value, Gtk.Widget):
                key = "Gtk." + name
                if key not in GTK_MAPPING:
                    missing.append(key)
        except TypeError:
            pass

    print "Following widget sublasses are missing an image:"
    print missing

    resp = requests.get("http://git.gnome.org/browse/gtk+/plain/docs/reference/gtk/images/")
    mapped_images = GTK_MAPPING.values()
    not_mapped = []
    for image in set(re.findall("([^>/]+?)\.png", resp.text)):
        if image not in mapped_images:
            not_mapped.append(image)
    not_mapped.sort()

    print "Following images on the server aren't linked to a widget"
    print "http://git.gnome.org/browse/gtk+/plain/docs/reference/gtk/images/"
    print not_mapped

    pool = Pool(20)
    for key, data in pool.imap_unordered(fetch, mapping.items()):
        dest_path = os.path.join(dest, key + ".png")
        with open(dest_path, "wb") as h:
            h.write(data)


if __name__ == "__main__":
    main(DESTINATION, MAPPING)
