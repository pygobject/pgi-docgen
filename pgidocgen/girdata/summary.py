# Copyright 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from BeautifulSoup import BeautifulStoneSoup

from .util import get_doap_path, load_debian


class ProjectSummary(object):

    name = None
    description = None
    homepage = None
    bugtracker = None
    repositories = []
    mailinglists = []
    dependencies = []
    debian_package = None


def get_project_summary(namespace, version):
    """Returns a summary extracted from a doap file"""

    ps = ProjectSummary()

    doap_path = get_doap_path(namespace)
    if os.path.exists(doap_path):

        with open(doap_path, "rb") as h:
            soup = BeautifulStoneSoup(h)

        name = soup.find("name")
        shortdesc = soup.find("shortdesc")
        description = soup.find("description")
        mailing_lists = soup.findAll("mailing-list")
        homepage = soup.find("homepage")
        bug_database = soup.find("bug-database")
        repository = soup.find("repository")
        repositories = (repository and repository.findAll("browse")) or []

        if name:
            ps.name = name.string
            if shortdesc:
                ps.name += " (%s)" % shortdesc.string.strip()

        if description:
            ps.description = description.string

        if homepage:
            ps.homepage = homepage["rdf:resource"]

        if bug_database:
            ps.bugtracker = bug_database["rdf:resource"]

        ps.repositories = [
            (r["rdf:resource"], r["rdf:resource"]) for r in repositories]

        def strip_mailto(s):
            if s.startswith("mailto:"):
                return s[7:]
            return s

        ps.mailinglists = [
            (strip_mailto(r["rdf:resource"]), r["rdf:resource"])
            for r in mailing_lists]

    key = "%s-%s" % (namespace, version)
    deb_info = load_debian()
    if key not in deb_info:
        return ps

    info = deb_info[key]

    if not ps.name:
        ps.name = info["lib"]
        if info["summary"]:
            ps.name += " (" + info["summary"] + ")"

    if not ps.homepage:
        ps.homepage = info["homepage"]

    if not ps.description:
        ps.description = info["description"]

    ps.debian_package = info["debian_package"]

    return ps
