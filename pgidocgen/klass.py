# Copyright 2013,2014 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util
from .fields import FieldsMixin
from .util import get_csv_line, fake_subclasses, get_template

_main_template = get_template("""\
{% if is_interface %}
==========
Interfaces
==========
{% else %}
=======
Classes
=======
{% endif %}

.. toctree::
    :maxdepth: 1

    {% for name in names %}
    {{ name }}
    {% endfor %}

""")


_sub_template = get_template("""\
{{ "=" * cls_name|length }}
{{ cls_name }}
{{ "=" * cls_name|length }}

.. inheritance-diagram:: {{ cls_name }}

{% if has_image %}
Example
-------

.. image:: ../_clsimages/{{ cls_name }}.png

{% endif %}

{% if subclass_names %}
    {% if is_interface %}
:Implementations:
    {% else %}
:Subclasses:
    {% endif %}
    {% for name in subclass_names %}
    :class:`{{ name }}`{% if not loop.last %}, {% endif %}
    {% endfor %}
{% endif %}


.. _{{ cls_name }}.methods:

Methods
-------

{% if methods_inherited %}
{{ methods_inherited }}

{% endif %}
{% if method_names %}
.. autosummary::

    {% for name in method_names %}
    {{ name }}
    {% endfor %}

{% endif %}
{% if not methods_inherited and not method_names %}
None

{% endif %}


.. _{{ cls_name }}.vfuncs:

Virtual Methods
---------------

{% if vfuncs_inherited %}
{{ vfuncs_inherited }}

{% endif %}
{% if vfunc_names %}
.. autosummary::

    {% for name in vfunc_names %}
    {{ name }}
    {% endfor %}

{% endif %}
{% if not vfuncs_inherited and not vfunc_names %}
None

{% endif %}


.. _{{ cls_name }}.props:

Properties
----------

{% if props_inherited %}
{{ props_inherited }}

{% endif %}
{% if prop_lines %}
.. csv-table::
    :header: "Name", "Type", "Flags", "Short Description"
    :widths: 1, 1, 1, 100

    {% for line in prop_lines %}
    {{ line }}
    {% endfor %}

{% endif %}
{% if not props_inherited and not prop_lines %}
None

{% endif %}


{% if child_prop_lines or child_props_inherited %}

.. _{{ cls_name }}.child-props:

Child Properties
----------------

{% if child_props_inherited %}
{{ child_props_inherited }}

{% endif %}
{% if child_prop_lines %}
.. csv-table::
    :header: "Name", "Type", "Default", "Flags", "Short Description"
    :widths: 1, 1, 1, 1, 100

    {% for line in child_prop_lines %}
    {{ line }}
    {% endfor %}

{% endif %}
{% endif %}

{% if style_prop_lines or style_props_inherited %}

.. _{{ cls_name }}.style-props:

Style Properties
----------------

{% if style_props_inherited %}
{{ style_props_inherited }}

{% endif %}
{% if style_prop_lines %}
.. csv-table::
    :header: "Name", "Type", "Default", "Flags", "Short Description"
    :widths: 1, 1, 1, 1, 100

    {% for line in style_prop_lines %}
    {{ line }}
    {% endfor %}

{% endif %}
{% endif %}


.. _{{ cls_name }}.signals:

Signals
-------

{% if sigs_inherited %}
{{ sigs_inherited }}

{% endif %}
{% if sig_lines %}
.. csv-table::
    :header: "Name", "Short Description"
    :widths: 30, 70

    {% for line in sig_lines %}
    {{ line }}
    {% endfor %}

{% endif %}
{% if not sigs_inherited and not sig_lines %}
None

{% endif %}


{{ field_table }}


Class Details
-------------

.. autoclass:: {{ cls_name }}
    {% if not is_base %}
    :show-inheritance:
    {% endif %}
    :members:
    :undoc-members:

{% if signals %}
Signal Details
--------------

{% for signal in signals %}
.. py:function:: {{ cls_name }}.signals.{{ signal.sig }}

    :Signal Name: ``{{ signal.name }}``
    :Flags: {{ signal.flags_string }}

    {{ signal.desc|indent(4, False) }}


{% endfor %}
{% endif %}


{% if properties %}
Property Details
----------------

{% for prop in properties %}
.. py:data:: {{ cls_name }}.props.{{ prop.attr_name }}

    :Name: ``{{ prop.name }}``
    :Type: {{ prop.type_desc }}
    :Default Value: {{ prop.value_desc }}
    :Flags: {{ prop.flags_string }}


    {{ prop.desc|indent(4, False) }}


{% endfor %}
{% endif %}

""")


_pysub_template = get_template("""\
{{ "=" * cls_name|length }}
{{ cls_name }}
{{ "=" * cls_name|length }}

.. autoclass:: {{ cls_name }}
    :members:
    :undoc-members:

""")


class ClassGenerator(util.Generator, FieldsMixin):
    """For GObjects an GInterfaces"""

    def __init__(self, repo):
        self._classes = {}  # cls -> code
        self._ifaces = {}
        self._methods = {}  # cls -> [methods]
        self._props = {}  # cls -> [prop]
        self._child_props = {}  # cls -> [prop]
        self._style_props = {}  # cls -> [prop]
        self._sigs = {}  # cls -> [sig]
        self._py_class = set()

        self.repo = repo

    def add_class(self, obj, code, py_class=False):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._classes[obj] = code
        if py_class:
            self._py_class.add(obj)

    def add_interface(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        self._ifaces[obj] = code

    def add_methods(self, cls_obj, methods):
        assert cls_obj not in self._methods

        self._methods[cls_obj] = methods

    def _get_inheritance_list(self, cls, ref_suffix):
        if ref_suffix == "methods":
            cfunc = self.repo.get_method_count
        elif ref_suffix == "vfuncs":
            cfunc = self.repo.get_vfunc_count
        elif ref_suffix == "props":
            cfunc = self.repo.get_property_count
        elif ref_suffix == "signals":
            cfunc = self.repo.get_signal_count
        elif ref_suffix == "fields":
            cfunc = self.repo.get_field_count
        elif ref_suffix == "child-props":
            cfunc = self.repo.get_child_property_count
        elif ref_suffix == "style-props":
            cfunc = self.repo.get_style_property_count
        else:
            assert 0

        bases = []
        for base in util.fake_mro(cls):
            if base is object or base is cls:
                continue
            num = cfunc(base)
            if num:
                name = base.__module__ + "." + base.__name__
                bases.append(
                    ":ref:`%s (%d)<%s.%s>`" % (name, num, name, ref_suffix))

        if bases:
            return """

:Inherited: %s

""" % ", ".join(bases)
        else:
            return ""

    def add_properties(self, cls, props):
        assert cls not in self._props

        if props:
            self._props[cls] = props

    def add_child_properties(self, cls, props):
        assert cls not in self._child_props

        if props:
            self._child_props[cls] = props

    def add_style_properties(self, cls, props):
        assert cls not in self._style_props

        if props:
            self._style_props[cls] = props

    def add_signals(self, cls, sigs):
        assert cls not in self._sigs

        if sigs:
            self._sigs[cls] = sigs

    def get_names(self):
        names = []
        if self._ifaces:
            names.append("interfaces/index.rst")
        if self._classes:
            names.append("classes/index.rst")
        return names

    def is_empty(self):
        return not bool(self._classes) and not bool(self._ifaces)

    def get_mro(self, cls):
        return [c for c in cls.__mro__ if
                c in self._classes or c in self._ifaces]

    def write(self, dir_, module_fileobj):
        if self._ifaces:
            self._write(module_fileobj, os.path.join(dir_, "interfaces"),
                        self._ifaces, True)

        if self._classes:
            self._write(module_fileobj, os.path.join(dir_, "classes"),
                        self._classes, False)

    def _write(self, module_fileobj, sub_dir, classes, is_interface):
        os.mkdir(sub_dir)
        index_path = os.path.join(sub_dir, "index.rst")

        # write the code
        for cls in classes:
            module_fileobj.write(classes[cls])

            methods = self._methods.get(cls, [])

            def method_sort_key(m):
                return m.is_vfunc, not m.is_static, m.name

            for method in sorted(methods, key=method_sort_key):
                code = method.code
                if not isinstance(code, bytes):
                    code = code.encode("utf-8")
                module_fileobj.write(util.indent(code) + "\n")

        classes = sorted(classes.keys(), key=lambda x: x.__name__)

        # index rst
        with open(index_path, "wb") as h:
            names = [cls.__name__ for cls in classes]
            text = _main_template.render(
                is_interface=is_interface, names=names)
            h.write(text.encode("utf-8"))

        for cls in classes:
            self._write_class(sub_dir, cls, is_interface)

    def _get_subclasses(self, cls):
        subclasses = []
        for sub in fake_subclasses(cls):
            # don't include things we happened to import
            if sub not in self._classes and sub not in self._ifaces:
                continue
            subclasses.append(sub)
        return set(subclasses)

    def _write_class(self, sub_dir, cls, is_interface):

        def get_name(cls):
            return cls.__module__ + "." + cls.__name__

        with open(os.path.join(sub_dir, cls.__name__) + ".rst", "wb") as h:
            cls_name = get_name(cls)
            is_base = util.is_base(cls)

            # special case classes which don't inherit from any GI class
            # and are defined in the overrides:
            # e.g. Gtk.TreeModelRow, GObject.ParamSpec
            if cls in self._py_class:
                text = _pysub_template.render(cls_name=cls_name)
                h.write(text.encode("utf-8"))
                return

            # SUBCLASSES
            subclasses = self._get_subclasses(cls)
            subclass_names = sorted([get_name(c) for c in subclasses])

            # IMAGE
            image_path = os.path.join(
                "data", "clsimages", "%s-%s" % (
                    self.repo.namespace, self.repo.version),
                "%s.png" % cls_name)
            has_image = os.path.exists(image_path)

            # METHODS

            # sort static methods first, then by name
            def sort_func(m):
                return not m.is_static, m.name

            methods_inherited = self._get_inheritance_list(cls, "methods")
            methods = sorted(
                [m for m in self._methods.get(cls, []) if not m.is_vfunc],
                key=sort_func)

            method_names = []
            for method in methods:
                method_names.append(cls_name + "." + method.name)

            # VFUNCS

            # sort static methods first, then by name
            def sort_func(m):
                return not m.is_static, m.name

            vfuncs_inherited = self._get_inheritance_list(cls, "vfuncs")
            vfuncs = sorted(
                [m for m in self._methods.get(cls, []) if m.is_vfunc],
                 key=sort_func)
            vfunc_names = []
            for method in vfuncs:
                vfunc_names.append(cls_name + "." + method.name)

            # PROPERTIES
            props_inherited = self._get_inheritance_list(cls, "props")
            props = sorted(self._props.get(cls, []), key=lambda p: p.name)

            prop_lines = []
            for p in props:
                fstr = p.flags_string
                rst_target = cls_name + ".props." + p.attr_name
                name = ":py:data:`%s<%s>`" % (p.name, rst_target)
                line = get_csv_line([name, p.type_desc, fstr, p.short_desc])
                prop_lines.append(line)

            # CHILD PROPERTIES
            child_props_inherited = self._get_inheritance_list(
                cls, "child-props")
            child_props = sorted(
                self._child_props.get(cls, []), key=lambda p: p.name)
            child_prop_lines = []
            for p in child_props:
                name = "``%s``" % p.name
                line = get_csv_line(
                    [name, p.type_desc, p.value_desc,
                     p.flags_string, p.short_desc])
                child_prop_lines.append(line)

            # STYLE PROPERTIES
            style_props_inherited = self._get_inheritance_list(
                cls, "style-props")
            style_props = sorted(
                self._style_props.get(cls, []), key=lambda p: p.name)
            style_prop_lines = []
            for p in style_props:
                name = "``%s``" % p.name
                line = get_csv_line(
                    [name, p.type_desc, p.value_desc,
                     p.flags_string, p.short_desc])
                style_prop_lines.append(line)

            # SIGNALS
            sigs_inherited = self._get_inheritance_list(cls, "signals")
            sigs = sorted(self._sigs.get(cls, []), key=lambda s: s.name)
            sig_lines = []
            for sig in sigs:
                rst_target = cls_name + ".signals." + sig.attr_name
                name_ref = ":py:func:`%s<%s>`" % (sig.name, rst_target)
                line = get_csv_line([name_ref, sig.short_desc])
                sig_lines.append(line)

            # FIELDS
            fields_inherited = self._get_inheritance_list(cls, "fields")
            field_table = self.get_field_table(cls, fields_inherited)

            # render
            text = _sub_template.render(
                cls_name=cls_name, is_interface=is_interface,
                subclass_names=subclass_names, has_image=has_image,
                methods_inherited=methods_inherited, method_names=method_names,
                vfuncs_inherited=vfuncs_inherited, vfunc_names=vfunc_names,
                props_inherited=props_inherited, prop_lines=prop_lines,
                child_props_inherited=child_props_inherited,
                child_prop_lines=child_prop_lines,
                style_props_inherited=style_props_inherited,
                style_prop_lines=style_prop_lines,
                sigs_inherited=sigs_inherited, sig_lines=sig_lines,
                field_table=field_table, is_base=is_base,
                signals=sigs, properties=props)

            h.write(text.encode("utf-8"))
