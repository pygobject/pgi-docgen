#!/usr/bin/python
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys
import argparse
import json
import urllib

import requests
from BeautifulSoup import BeautifulSoup
from multiprocessing import Pool

from pgidocgen.girdata import get_docref_path
from pgidocgen.girdata.library import LIBRARIES


def fetch_pages(lib):
    pages = set()
    keywords = set()
    r = requests.get(lib.devhelp_url)
    soup = BeautifulSoup(r.text)

    for tag in soup.findAll("sub"):
        page = tag["link"]
        if page.startswith(("index-", "api-index-",
                            "annotation-glossary", "ix")):
            continue
        if "#" in page:
            continue
        pages.add(page)

    for tag in soup.findAll("keyword"):
        keywords.add(tag["link"])


    return pages, keywords


def fetch_page(arg):
    lib, page, keywords = arg

    names = {}
    r = requests.get(lib.url + page)
    soup = BeautifulSoup(r.text)
    for link in soup.findAll("a"):
        if link.get("name") and "." not in link["name"]:
            url = page + "#" + link["name"]
            if url not in keywords:
                names[urllib.unquote(link["name"])] = lib.url + url
    return names, page


def main(argv):
    pool = Pool(20)

    parser = argparse.ArgumentParser(description='Fetch docrefs')
    parser.add_argument('namespace', nargs="*",
                        help='namespace including version e.g. Gtk-3.0')

    try:
        args = parser.parse_args(argv[1:])
    except SystemExit:
        raise SystemExit(1)

    if not args.namespace:
        libraries = LIBRARIES
    else:
        libraries = []
        for l in LIBRARIES:
            if l.namespace in args.namespace:
                libraries.append(l)
        if len(args.namespace) != len(libraries):
            print "Invalid namespaces in %s" % args.namespace
            raise SystemExit(1)

    for lib in libraries:
        pages, keywords = fetch_pages(lib)
        mapping = {}
        for names, page in pool.imap_unordered(
                fetch_page, [(lib, p, keywords) for p in pages]):
            print page
            mapping.update(names)

        ns = lib.namespace
        namespace, version = ns.split("-")
        with open(get_docref_path(namespace, version), "wb") as h:
            h.write(json.dumps(mapping, sort_keys=True, indent=4))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
