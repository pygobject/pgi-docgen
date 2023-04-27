# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os
import requests
from multiprocessing.pool import ThreadPool

from ..girdata import get_class_image_dir
from ..util import progress


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "update-images-4", help="Update the class images for gtk4")
    parser.set_defaults(func=main)


GTK_MAPPING = {
    "Button": "button",
    "Switch": "switch",
    "ToggleButton": "toggle-button",
    "CheckButton": "check-button",
    "LinkButton": "link-button",
    "MenuButton": "menu-button",
    "Entry": "entry",
    "SearchEntry": "search-entry",
    "Label": "label",
    "ComboBox": "combo-box",
    "ComboBoxText": "combo-box-text",
    "InfoBar": "info-bar",
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
    "Stack": "stack",
    "StackSwitcher": "stackswitcher",
    "ListBox": "list-box",
    "FlowBox": "flow-box",
    "ActionBar": "action-bar",
    "ComboBoxText": "combo-box-text",
    "SearchBar": "search-bar",
    "Frame": "frame",
    "Sidebar": "sidebar",
    "GLArea": "glarea",
    "LockButton": "lockbutton",
    "Box": "box",
    "Calendar": "calendar",
    "Dialog": "dialog",
    "MediaControls": "media-controls",
    "CenterBox": "centerbox",
    "DrawingArea": "drawingarea",
    "EmojiChooser": "emojichooser",
    "Expander": "expander",
    "FontDialogButton": "font-button",
    "Grid": "grid",
    "Video": "video",
    "WindowControls": "windowcontrols",
    "ShortcutsWindow": "shortcuts-window",
}

GTK_URL = ("https://gitlab.gnome.org/GNOME/gtk/raw/main/docs/"
           "reference/gtk/images/%s.png")

MAPPING = dict([(k, GTK_URL % v) for k, v in GTK_MAPPING.items()])


def fetch(args):
    key, url = args
    resp = requests.get(url)
    resp.raise_for_status()
    return key, resp.content


def main(args):
    import pgi
    pgi.require_version("Gtk", "4.0")

    from pgi.repository import Gtk

    dest = get_class_image_dir("Gtk", "4.0")
    mapping = MAPPING

    # make sure there are no typos in the mapping
    for key in mapping.keys():
        if not hasattr(Gtk, key):
            print(key, "missing...")

    missing = []
    for name in dir(Gtk):
        value = getattr(Gtk, name)
        try:
            if issubclass(value, Gtk.Widget):
                if name not in GTK_MAPPING:
                    missing.append(name)
        except TypeError:
            pass

    print("Following widget sublasses are missing an image:")
    print(missing)

    with ThreadPool(20) as pool:
        items = mapping.items()
        with progress(len(items)) as update:
            for i, (key, data) in enumerate(pool.imap_unordered(fetch, items)):
                update(i + 1)
                os.makedirs(dest, exist_ok=True)
                dest_path = os.path.join(dest, key + ".png")
                with open(dest_path, "wb") as h:
                    h.write(data)
