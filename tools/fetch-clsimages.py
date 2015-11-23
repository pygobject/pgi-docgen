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
from pgidocgen.girdata import get_class_image_dir


DESTINATION = get_class_image_dir("Gtk", "3.0")

GTK_MAPPING = {
    "Button": "button",
    "Switch": "switch",
    "ToggleButton": "toggle-button",
    "CheckButton": "check-button",
    "LinkButton": "link-button",
    "MenuButton": "menu-button",
    "LockButton": "lock-button",
    "Entry": "entry",
    "SearchEntry": "search-entry",
    "RadioButton": "radio-group",
    "Label": "label",
    "AccelLabel": "accel-label",
    "ComboBox": "combo-box",
    "ComboBoxText": "combo-box-text",
    "InfoBar": "info-bar",
    "RecentChooserDialog": "recentchooserdialog",
    "TextView": "multiline-text",
    "TreeView": "list-and-tree",
    "IconView": "icon-view",
    "ColorButton": "color-button",
    "FontButton": "font-button",
    "FileChooserButton": "file-button",
    "Separator": "separator",
    "Paned": "panes",
    "Frame": "frame",
    "Window": "window",
    "FileChooser": "filechooser",
    "PageSetup": "pagesetupdialog",
    "Toolbar": "toolbar",
    "ToolPalette": "toolpalette",
    "MenuBar": "menubar",
    "MessageDialog": "messagedialog",
    "AboutDialog": "aboutdialog",
    "Notebook": "notebook",
    "ProgressBar": "progressbar",
    "LevelBar": "levelbar",
    "ScrolledWindow": "scrolledwindow",
    "Scrollbar": "scrollbar",
    "SpinButton": "spinbutton",
    "Statusbar": "statusbar",
    "Scale": "scales",
    "Image": "image",
    "Spinner": "spinner",
    "VolumeButton": "volumebutton",
    "Assistant": "assistant",
    "AppChooserButton": "appchooserbutton",
    "AppChooserDialog": "appchooserdialog",
    "FontChooserDialog": "fontchooser",
    "ColorChooserDialog": "colorchooser",
    "HeaderBar": "headerbar",
    "PlacesSidebar": "placessidebar",
    "Stack": "stack",
    "StackSwitcher": "stackswitcher",
    "ListBox": "list-box",
    "FlowBox": "flow-box",
    "ActionBar": "action-bar",
    "ComboBoxText": "combo-box-text",
    "PlacesSidebar": "placessidebar",
    "SearchBar": "search-bar",
    "Frame": "frame",
    "Sidebar": "sidebar",
    "GLArea": "glarea",
    "LockButton": "lockbutton",
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
        if not hasattr(Gtk, key):
            print key, "missing..."

    missing = []
    for name in dir(Gtk):
        value = getattr(Gtk, name)
        try:
            if issubclass(value, Gtk.Widget):
                if name not in GTK_MAPPING:
                    missing.append(name)
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
