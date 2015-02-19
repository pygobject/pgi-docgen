# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from __future__ import absolute_import

import markdown
from BeautifulSoup import BeautifulSoup, Tag


def _md_tag(tag):
    if not isinstance(tag, Tag):
        return [tag.string.strip("\n")]
    if tag.name == "p":
        return ["<para>"] + _md_list(tag) + ["</para>"]
    elif tag.name == "a":
        return ['<ulink url="%s">%s</ulink>' % (tag["href"], _md_text(tag))]
    elif tag.name == "ul":
        l = ["<itemizedlist>"]
        for sub in tag:
            if isinstance(sub, Tag):
                l.append("<listitem>%s</listitem>" % _md_text(sub))
        l.append("</itemizedlist>")
        return l
    elif tag.name == "code":
        return ["<literal>%s</literal>" % _md_text(tag)]
    elif tag.name == "h1":
        text = _md_text(tag)
        return ["<title>%s</title>" % text]
    elif tag.name == "h2":
        text = _md_text(tag)
        return ["<subtitle>%s</subtitle>" % text]
    elif tag.name == "h3":
        text = _md_text(tag)
        return ["<subtitle>%s</subtitle>" % text]
    elif tag.name == "em":
        return ["<emphasis>%s</emphasis>" % _md_text(tag)]
    return [_md_text(tag)]


def _md_text(tag):
    return " ".join(filter(None, _md_list(tag)))


def _md_list(soup):
    out = []
    for item in soup:
        out.extend(_md_tag(item))
    return out


def markdown2docbook(md):
    html = markdown.markdown(md, extensions=['attr_list'])
    soup = BeautifulSoup(html)
    return "\n".join(_md_list(soup))
