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
        return _md_list(tag)
    elif tag.name == "a":
        return ["`%s <%s>`__" % (_md_text(tag), tag["href"])]
    elif tag.name == "ul":
        l = []
        for sub in tag:
            if isinstance(sub, Tag):
                l.append("* %s" % _md_text(sub))
        return l
    elif tag.name == "h1":
        text = _md_text(tag)
        return [text, "=" * len(text)]
    elif tag.name == "h2":
        text = _md_text(tag)
        return [text, "-" * len(text)]
    elif tag.name == "h3":
        text = _md_text(tag)
        return [text, "^" * len(text)]
    elif tag.name == "em":
        return "*%s*" % _md_text(tag)
    return _md_text(tag)


def _md_text(tag):
    return "".join(_md_list(tag))


def _md_list(soup):
    out = []
    for item in soup:
        out.extend(_md_tag(item))
    return out


def markdown2rest(md):
    html = markdown.markdown(md, extensions=['attr_list'])
    soup = BeautifulSoup(html)
    return "\n".join(_md_list(soup))
