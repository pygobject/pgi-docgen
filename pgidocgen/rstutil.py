# # -*- coding: utf-8 -*-
# Copyright 2016 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


def bold(text):
    return "**%s**" % text.replace("\\", "\\\\").replace("*", "\\*")


def field_name(*parts):
    text = " ".join(parts)
    return ":%s:" % text.replace(
        "\\", "\\\\").replace(":", "\\:").replace("*", "\\*")
