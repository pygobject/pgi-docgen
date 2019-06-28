# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from multiprocessing.pool import ThreadPool

import requests

from ..util import get_gir_files, progress
from ..girdata import PROJECTS, get_doap_path


def add_parser(subparsers):
    parser = subparsers.add_parser(
        "update-doap", help="Update the doap files")
    parser.set_defaults(func=main)


def fetch(project):
    resp = requests.get(project.doap)
    if resp.status_code != requests.codes.ok:
        raise Exception(project.doap)
    return resp.content, project


def main(args):
    ns_list = set([n.split("-")[0] for n in get_gir_files().keys()])
    for p in PROJECTS:
        ns_list -= set(p.namespaces)

    print("Missing: %s" % ", ".join(sorted(ns_list)))

    projects = [p for p in PROJECTS if p.doap]
    with ThreadPool(20) as pool:
        with progress(len(projects)) as update:
            for i, (content, project) in enumerate(pool.imap_unordered(fetch, projects)):
                update(i + 1)
                for ns in project.namespaces:
                    path = get_doap_path(ns)
                    with open(path, 'wb') as h:
                        h.write(content)
