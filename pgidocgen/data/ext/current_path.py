# Copyright 2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


def pgi_docgen_path(app, pagename, templatename, context, doctree):
    path = context["project"].replace(" ", "-") + "/" + pagename + ".html"
    context['pgi_docgen_path'] = path


def setup(app):
    app.connect('html-page-context', pgi_docgen_path)
