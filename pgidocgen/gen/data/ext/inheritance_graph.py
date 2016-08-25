# -*- coding: utf-8 -*-

import os

from docutils import nodes

from sphinx.ext.graphviz import render_dot, GraphvizError
from sphinx.util.compat import Directive


def generate_dot(graph, colors, urls={}):
    g_attrs = {
        'rankdir': 'TB',
        'size': '""',
        'bgcolor': 'transparent',
    }

    e_attrs = {
        'arrowsize': 0.5,
        'style': '"setlinewidth(0.5)"',
    }

    n_attrs = {
        'shape': 'box',
        'fontsize': 8.5,
        'height': 0.25,
        'color': 'gray70',
        'fontname': 'inherit',
        'style': 'rounded',
    }

    def format_graph_attrs(attrs):
        return ''.join(['%s=%s;\n' % x for x in attrs.items()])

    def format_node_attrs(attrs):
        return ','.join(['%s=%s' % x for x in attrs.items()])

    res = []
    res.append('digraph g {\n')
    res.append(format_graph_attrs(g_attrs))

    for fullname, url in urls.items():
        this_node_attrs = n_attrs.copy()
        this_node_attrs['URL'] = '"%s"' % url

        if fullname in colors:
            this_node_attrs["color"] = '"%s"' % colors[fullname]
        res.append('  "%s" [%s];\n' %
                   (fullname, format_node_attrs(this_node_attrs)))

    for a, b in graph:
        res.append('  "%s" -> "%s" [%s];\n' %
                   (a, b, format_node_attrs(e_attrs)))

    res.append('}\n')
    return ''.join(res)


class inheritance_graph(nodes.General, nodes.Element):
    pass


class InheritanceGraph(Directive):

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        node = inheritance_graph()

        class_name = self.arguments[0]

        classes = set()
        classes.add(class_name)
        graph = []
        colors = {}
        for line in self.content:
            if not line.strip():
                continue
            parts = map(unicode.strip, line.split("->"))
            if len(parts) != 2:
                parts = map(unicode.strip, line.split(":"))
                assert len(parts) == 2
                colors[parts[0]] = parts[1]
                continue
            classes.update(parts)
            graph.append(parts)

        node.document = self.state.document
        env = self.state.document.settings.env
        class_role = env.get_domain('py').role('class')
        classes = sorted(classes)

        for name in classes:
            refnodes, x = class_role(
                'class', ':class:`%s`' % name, name, 0, self.state)
            node.extend(refnodes)

        node['graph'] = graph
        node['content'] = class_name
        node['graph_classes'] = classes
        node['graph_colors'] = colors

        return [node]


def render_dot_html(self, node, code, options, prefix='graphviz',
                    imgcls=None, alt=None):
    try:
        fname, outfn = render_dot(self, code, options, "svg", prefix)
    except GraphvizError, exc:
        self.builder.warn('dot code %r: ' % code + str(exc))
        raise nodes.SkipNode

    inline = node.get('inline', False)
    if inline:
        wrapper = 'span'
    else:
        wrapper = 'p'

    self.body.append(self.starttag(node, wrapper, CLASS='graphviz'))
    if fname is None:
        self.body.append(self.encode(code))
    else:
        # inline the svg
        with open(outfn, "rb") as h:
            data = h.read().decode("utf-8")
            data = data[data.find("<svg"):]
        os.remove(outfn)
        self.body.append(data)

    self.body.append('</%s>\n' % wrapper)
    raise nodes.SkipNode


def html_visit_inheritance_graph(self, node):
    graph = node['graph']
    class_name = node['content']
    classes = node['graph_classes']
    colors = node['graph_colors']

    urls = {}
    for fullname, child in zip(classes, node):
        try:
            url = child.get('refuri') or '#' + child['refid']
        except KeyError:
            url = ""
        urls[fullname] = url

    dotcode = generate_dot(graph, colors, urls)
    render_dot_html(self, node, dotcode, {}, 'inheritance', 'inheritance',
                    alt='Inheritance diagram of ' + class_name)
    raise nodes.SkipNode


def skip(self, node):
    raise nodes.SkipNode


def setup(app):
    app.setup_extension('sphinx.ext.graphviz')
    app.add_node(
        inheritance_graph,
        latex=(skip, None),
        html=(html_visit_inheritance_graph, None),
        text=(skip, None),
        man=(skip, None),
        texinfo=(skip, None))
    app.add_directive('inheritance-graph', InheritanceGraph)

    return {"parallel_read_safe": True}
