#!/usr/bin/python
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import sys
import json
import urllib

import requests
from BeautifulSoup import BeautifulSoup
from multiprocessing import Pool

from pgidocgen.girdata import GTK_DOCS, get_docref_path


def fetch_pages(doc):
    pages = set()
    keywords = set()
    r = requests.get(doc.devhelp_url)
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
    doc, page, keywords = arg

    names = {}
    r = requests.get(doc.url + page)
    soup = BeautifulSoup(r.text)
    for link in soup.findAll("a"):
        if link.get("name") and "." not in link["name"]:
            url = page + "#" + link["name"]
            if url not in keywords:
                names[urllib.unquote(link["name"])] = doc.url + url
    return names, page


def main(argv):
    pool = Pool(20)

    for doc in GTK_DOCS:
        pages, keywords = fetch_pages(doc)
        mapping = {}
        for names, page in pool.imap_unordered(
                fetch_page, [(doc, p, keywords) for p in pages]):
            print page
            mapping.update(names)

        for ns in doc.namespaces:
            namespace, version = ns.split("-")
            with open(get_docref_path(namespace, version), "wb") as h:
                h.write(json.dumps(mapping, sort_keys=True, indent=4))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
