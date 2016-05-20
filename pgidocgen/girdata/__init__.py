# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""Database containing additional optional info about common gir files.

The gir files don't contain all the info we would like to have so this is a
collection of various information about the relation of the girs and their
projects and additional data fetched from other sources.

See tools/fetch-*.py for scripts which updates some of this info from external
sources.
"""

from .summary import get_project_summary
from .project import Project, PROJECTS
from .library import Library
from .util import get_doap_dir, get_doap_path, get_debian_path, \
    get_docref_dir, get_docref_path, get_class_image_dir, \
    get_class_image_path, load_doc_references


get_project_summary, Project, Library, PROJECTS, get_debian_path,
get_doap_dir, get_doap_path, get_docref_dir, get_docref_path,
get_class_image_dir, get_class_image_path, load_doc_references
