# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
This toctree() replacement doesn't remove all entries below
the specified maxdepth, but keeps all current entries > maxdepth.
"""


from sphinx import addnodes
from docutils import nodes


def init_pruned_toctree(app, pagename, templatename, context, doctree):

    def _get_toctree(collapse=True, **kwds):

        # save maxdepth and reset it since we prune ourself below
        maxdepth = kwds.get("maxdepth", -1)
        kwds["maxdepth"] = -1
        toctree = app.env.get_toctree_for(
            pagename, app.builder, collapse, **kwds)

        # remove any non current nodes after the specified maxdepth level
        def _prune_non_current(toctree, depth):

            for node in toctree.children[:]:
                if isinstance(node, (addnodes.compact_paragraph,
                                     nodes.list_item)):
                    next_depth = depth
                elif isinstance(node, nodes.bullet_list):
                    next_depth = depth - 1
                else:
                    continue

                if depth < 0 and "current" not in node["classes"]:
                    node.parent.remove(node)
                else:
                    _prune_non_current(node, next_depth)

        # maxdepth == -1 means no pruning
        if maxdepth >= 0:
            _prune_non_current(toctree, maxdepth)

        return app.builder.render_partial(toctree)['fragment']
    context['pruned_toctree'] = _get_toctree


def setup(app):
    app.connect('html-page-context', init_pruned_toctree)
