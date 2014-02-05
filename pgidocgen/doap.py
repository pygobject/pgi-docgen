# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from BeautifulSoup import BeautifulStoneSoup

from . import util


def get_project_summary(namespace, version):
    """Returns a reST summary extracted from a doap file"""

    key = "%s-%s" % (namespace, version)
    doap_path = os.path.join("doap", key)
    if not os.path.exists(doap_path):
        return u""

    soup = BeautifulStoneSoup(open(doap_path, "rb"))

    name = soup.find("name")
    shortdesc = soup.find("shortdesc")
    description = soup.find("description")
    mailing_lists = soup.findAll("mailing-list")
    homepage = soup.find("homepage")
    bug_database = soup.find("bug-database")
    repository = soup.find("repository")
    repositories = (repository and repository.findAll("browse")) or []

    to_sub = lambda x: util.indent(util.force_unindent(x))

    summ = []

    if name:
        name_text = ":Parent Project:\n%s" % to_sub(name.string)
        if shortdesc:
            name_text += " (%s)" % shortdesc.string.strip()
        summ.append(name_text)

    if description:
        summ.append(":Description:\n%s" % to_sub(description.string))

    if homepage:
        summ.append(":Homepage:\n%s" % to_sub(homepage["rdf:resource"]))

    if bug_database:
        summ.append(":Bug Tracker:\n%s" % to_sub(bug_database["rdf:resource"]))

    if len(repositories) == 1:
        l = repositories[0]
        summ.append(":Repository:\n%s" % to_sub(l["rdf:resource"]))
    elif len(mailing_lists) > 1:
        repo_text = ":Repositories:\n"
        for r in repositories:
            repo_text += "    * %s\n" % r["rdf:resource"]
        summ.append(repo_text)

    if len(mailing_lists) == 1:
        l = mailing_lists[0]
        summ.append(":Mailing List:\n%s" % to_sub(l["rdf:resource"]))
    elif len(mailing_lists) > 1:
        ml_text = ":Mailing Lists:\n"
        for l in mailing_lists:
            ml_text += "    * %s\n" % l["rdf:resource"]
        summ.append(ml_text)


    return "\n".join(summ)
