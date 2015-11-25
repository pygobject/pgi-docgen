# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
This is a partial Python port of the markdown code from gtk-doc.

See https://git.gnome.org/browse/gtk-doc/commit/gtkdoc-mkdb.in?id=c567d9e28c355f43faeba61fb81fd16fc74cf062
"""

import re


MD_TEXT_LEVEL_ELEMENTS = {
    "literal", "emphasis", "envar", "filename", "firstterm", "footnote",
    "function", "manvolnum", "option", "replaceable", "structfield",
    "structname", "title", "varname",
}


def ConvertMarkDown(symbol, text):
    text = MarkDownParse(text, symbol)
    return text


def MarkDownParse(text, symbol):
    text = re.sub(r"\r\n", r"\n", text)
    text = re.sub(r"\r", r"\n", text)

    lines = text.split(u"\n")
    text = MarkDownParseLines(lines, symbol, u"")

    return text


def MarkDownParseLines(linesref, symbol, context):
    lines = linesref

    blocks = MarkDownParseBlocks(lines, symbol, context)
    output = MarkDownOutputDocBook(blocks, symbol, context)

    return output


def MarkDownParseBlocks(linesref, symbol, context):
    md_blocks = []
    md_block = {"type": ""}

    for line in linesref:
        first_char = line[:1]

        if md_block["type"] == "markup":
            if not md_block["closed"]:
                if line.index(md_block["start"]) != -1:
                    md_block["depth"] += 1
                if line.index(md_block["end"]) != -1:
                    if md_block["depth"] > 0:
                        md_block["depth"] -= 1
                    else:
                        #("closing tag '$line'");
                        md_block["closed"] = 1
                        # TODO(ensonic): reparse inner text with MarkDownParseLines?
                md_block["text"] += "\n" + line
                #("add to markup");
                continue

        deindented_line = line
        deindented_line = re.sub(r"^\s+", "", deindented_line)

        if md_block["type"] == "heading":
            heading_match = re.search(
                r"^[#][ \t]+(.+?)[ \t]*[#]*[ \t]*(?:{#([^}]+)})?[ \t]*$",
                line)
            # a heading is ended by any level less than or equal
            if md_block["level"] == 1:
                if re.search(r"^={4,}[ \t]*$", line):
                    text = md_block["lines"].pop()
                    md_block["interrupted"] = 0
                    md_blocks.append(md_block)

                    md_block = {
                        "type": "heading",
                        "text": text,
                        "lines": [],
                        "level": 1,
                    }
                    continue
                elif heading_match:
                    md_block["interrupted"] = 0
                    md_blocks.append(md_block)
                    md_block = {
                        "type": "heading",
                        "text": heading_match.group(1),
                        "id": heading_match.group(2),
                        "lines": [],
                        "level": 1,
                    }
                    continue
                else:
                    # push lines into the block until the end is reached
                    md_block["lines"].append(line)
                    continue
            else:
                heading_match = re.search(
                    r"^([#]{1,2})[ \t]+(.+?)[ \t]*[#]*[ \t]*(?:{#([^}]+)})?[ \t]*$",
                    line)
                if re.search(r"^[=]{4,}[ \t]*$", line):
                    text = md_block["lines"].pop()
                    md_block["interrupted"] = 0
                    md_blocks.append(md_block)

                    md_block = {
                        "type": "heading",
                        "text": text,
                        "lines": [],
                        "level": 1,
                    }
                    continue
                elif re.search(r"^[-]{4,}[ \t]*$", line):
                    text = md_block["lines"].pop()
                    md_block["interrupted"] = 0
                    md_blocks.append(md_block)
                    md_block = {
                        "type": "heading",
                        "text": text,
                        "lines": [],
                        "level": 2,
                    }
                    continue
                elif heading_match:
                    md_block["interrupted"] = 0
                    md_blocks.append(md_block)

                    md_block = {
                        "type": "heading",
                        "text": heading_match.group(2),
                        "id": heading_match.group(3),
                        "lines": [],
                        "level": len(heading_match.group(1)),
                    }
                    continue
                else:
                    # push lines into the block until the end is reached
                    md_block["lines"].append(line)
                    continue
        elif md_block["type"] == "code":
            match = re.search(r"^[ \t]*\]\|(.*)", line)
            if match:
                md_blocks.append(md_block)
                md_block = {
                    "type": "paragraph",
                    "text": match.group(1),
                    "lines": [],
                }
            else:
                md_block["lines"].append(line)
            continue

        if deindented_line == "":
            md_block["interrupted"] = 1
            continue

        if md_block["type"] == "quote":
            if not md_block.get("interrupted"):
                line = re.sub(r"^[ ]*>[ ]?", "", line)
                md_block["lines"].append(line)
                continue
        elif md_block["type"] == "li":
            marker = md_block["marker"]
            marker_match = re.search(r"^([ ]{0,3})(%s)[ ](.*)" % marker, line)
            if marker_match:
                indentation = marker_match.group(1)
                if md_block["indentation"] != indentation:
                    md_block["lines"].append(line)
                else:
                    lines = marker_match.group(3)
                    ordered = md_block["ordered"]
                    lines = re.sub(r"^[ ]{0,4}", "", lines)
                    md_block["last"] = 0
                    md_blocks.append(md_block)
                    md_block = {
                        "type": "li",
                        "ordered": ordered,
                        "indentation": indentation,
                        "marker": marker,
                        "first": 0,
                        "last": 1,
                        "lines": [lines],
                    }
                continue

            if md_block.get("interrupted"):
                if first_char == " ":
                    md_block["lines"].append("")
                    line = re.sub(r"^[ ]{0,4}", "", line)
                    md_block["lines"].append(line)
                    md_block["interrupted"] = 0
                    continue
            else:
                line = re.sub(r"^[ ]{0,4}", "", line)
                md_block["lines"].append(line)
                continue

        # indentation sensitive types
        #("parsing '$line'");

        heading_match = re.search(
            r"^([#]{1,2})[ \t]+(.+?)[ \t]*[#]*[ \t]*(?:{#([^}]+)})?[ \t]*$",
            line)
        code_match = re.search(
            r'^[ \t]*\|\[[ ]*(?:<!-- language="([^"]+?)" -->)?', line)

        if heading_match:
            # atx heading (#)
            md_blocks.append(md_block)

            md_block = {
                "type": "heading",
                "text": heading_match.group(2),
                "id": heading_match.group(3),
                "lines": [],
                "level": len(heading_match.group(1)),
            }
            continue
        elif re.search(r"^={4,}[ \t]*$", line):
            # setext heading (====)

            if md_block["type"] == "paragraph" and md_block.get("interrupted"):
                md_blocks.append(md_block.copy())
                md_block["type"] = "heading"
                md_block["lines"] = []
                md_block["level"] = 1
            continue
        elif re.search(r"^-{4,}[ \t]*$", line):
            # setext heading (-----)

            if md_block["type"] == "paragraph" and md_block.get("interrupted"):
                md_blocks.append(md_block.copy())
                md_block["type"] = "heading"
                md_block["lines"] = []
                md_block["level"] = 2
            continue
        elif code_match:
            # code
            md_block["interrupted"] = 1
            md_blocks.append(md_block)
            md_block = {
                "type": "code",
                "language": code_match.group(1),
                "lines": [],
            }
            continue

        markup_match = re.search(r"^[ ]*<\??(\w+)[^>]*([\/\?])?[ \t]*>", line)
        li_match = re.search(r"^([ ]*)[*+-][ ](.*)", line)
        quote_match = re.search(r"^[ ]*>[ ]?(.*)", line)

        # indentation insensitive types
        if re.search(r"^[ ]*<!DOCTYPE", line):
            md_blocks.append(md_block)
            md_block = {
                "type": "markup",
                "text": deindented_line,
                "start": "<",
                "end": ">",
                "closed": 0,
                "depth": 0,
            }
        elif markup_match:
            # markup, including <?xml version="1.0"?>
            tag = markup_match.group(1)
            is_self_closing = len(markup_match.groups()) >= 2

            # skip link markdown
            # TODO(ensonic): consider adding more uri schemes (ftp, ...)
            if re.search(r"^https?", tag):
                #("skipping link '$tag'");
                pass
            else:
                # for TEXT_LEVEL_ELEMENTS, we want to keep them as-is in the
                # paragraph instead of creation a markdown block.
                scanning_for_end_of_text_level_tag = (
                    md_block["type"] == "paragraph" and
                    "start" in md_block and
                    not md_block.get("closed"))
                #("markup found '$tag', scanning $scanning_for_end_of_text_level_tag ?");
                if tag not in MD_TEXT_LEVEL_ELEMENTS and not scanning_for_end_of_text_level_tag:
                    md_blocks.append(md_block)

                    if is_self_closing:
                        #("self-closing docbook '$tag'");
                        md_block = {
                            "type": "self-closing tag",
                            "text": deindented_line,
                        }
                        is_self_closing = 0
                        continue

                    #("new markup '$tag'");
                    md_block = {
                        "type": "markup",
                        "text": deindented_line,
                        "start": "<" + tag + ">",
                        "end": "</" + tag + ">",
                        "closed": 0,
                        "depth": 0,
                    }
                    if re.search(r"<\/%s>" % tag, deindented_line):
                        md_block["closed"] = 1
                    continue
                else:
                    if tag in MD_TEXT_LEVEL_ELEMENTS:
                        #("text level docbook '$tag' in '".$md_block->{"type"}."' state");
                        # TODO(ensonic): handle nesting
                        if not scanning_for_end_of_text_level_tag:
                            if re.search(r"<\/%s>" % tag, deindented_line):
                                #("new text level markup '$tag'");
                                md_block["start"] = "<" + tag + ">"
                                md_block["end"] = "</" + tag + ">"
                                md_block["closed"] = 0
                                #("scanning for end of '$tag'");
                        else:
                            if md_block["end"] in deindented_line:
                                md_block["closed"] = 1
                                #("found end of '$tag'");
        elif li_match:
            # li
            md_blocks.append(md_block)
            lines = li_match.group(2)
            indentation = li_match.group(1)
            lines = re.sub(r"^[ ]{0,4}", "", lines)

            md_block = {
                "type": "li",
                "ordered": 0,
                "indentation": indentation,
                "marker": "[*+-]",
                "first": 1,
                "last": 1,
                "lines": [lines],
            }
            continue
        elif quote_match:
            md_blocks.append(md_block)
            md_block = {
                "type": "quote",
                "lines": [quote_match.group(1)],
            }
            continue

        # list item
        list_item_match = re.search("^([ ]{0,4})\d+[.][ ]+(.*)", line)
        if list_item_match:
            md_blocks.append(md_block)
            lines = list_item_match.group(2)
            indentation = list_item_match.group(1)
            lines = re.sub("^[ ]{0,4}", "", lines)

            md_block = {
                "type": "li",
                "ordered": 1,
                "indentation": indentation,
                "marker": "\\d+[.]",
                "first": 1,
                "last": 1,
                "lines": [lines],
            }
            continue

        # paragraph
        if md_block["type"] == "paragraph":
            if md_block.get("interrupted"):
                md_blocks.append(md_block)
                md_block = {
                    "type": "paragraph",
                    "interrupted": 0,
                    "text": line,
                }
                #("new paragraph due to interrupted");
            else:
                md_block["text"] += "\n" + line
                #("add to paragraph");
        else:
            md_blocks.append(md_block)
            md_block = {
                "type": "paragraph",
                "text": line,
            }
            #("new paragraph due to different block type");


    md_blocks.append(md_block)
    md_blocks.pop(0)

    return md_blocks


def ReplaceEntities(text, symbol):
    entities = [
        ["&lt;", "<"],
        ["&gt;", ">"],
        ["&ast;", "*"],
        ["&num;", "#"],
        ["&percnt;", "%"],
        ["&colon;", ":"],
        ["&quot;", "\""],
        ["&apos;", "'"],
        ["&nbsp;", " "],
        ["&amp;", "&"], # Do this last, or the others get messed up.
    ]

    # Expand entities in <programlisting> even inside CDATA since
    # we changed the definition of |[ to add CDATA
    for a, b in entities:
        text = re.sub(re.escape(a), b, text)

    return text;


def MarkDownParseSpanElements(text):
    # TODO
    return text


def ExpandAbbreviations(symbol, text):
    # TODO
    return text


def MarkDownOutputDocBook(blocksref, symbol, context):
    output = u""
    blocks = blocksref

    for block in blocks:
        if block["type"] == "paragraph":
            text = MarkDownParseSpanElements(block["text"])
            if context == "li" and output == "":
                if block.get("interrupted"):
                    output += "\n<para>" + text + "</para>\n"
                else:
                    output += "<para>" + text + "</para>"
                    if len(blocks) > 0:
                        output += "\n"
            else:
                output += "<para>" + text + "</para>\n"
        elif block["type"] == "heading":
            title = MarkDownParseSpanElements(block["text"])
            if block["level"] == 1:
                tag = "refsect2"
            else:
                tag = "refsect3"

            text = MarkDownParseLines(block["lines"], symbol, "heading")
            if block.get("id"):
                output += ("<%s id=\"" % tag) + block["id"] + "\">"
            else:
                output += "<%s>" % tag

            output += "<title>%s</title>%s</%s>\n" % (title, text, tag)
        elif block["type"] == "li":
            tag = "itemizedlist"

            if block["first"]:
                if block["ordered"]:
                    tag = "orderedlist"
                output += "<%s>\n" % tag

            if block.get("interrupted"):
                block["lines"].append("")

            text = MarkDownParseLines(block["lines"], symbol, "li")
            output += "<listitem>%s</listitem>\n" % text

            if block["last"]:
                if block["ordered"]:
                    tag = "orderedlist"
                output += "</%s>\n" % tag

        elif block["type"] == "quote":
            text = MarkDownParseLines(block["lines"], symbol, "quote")
            output += "<blockquote>\n%s</blockquote>\n" % text
        elif block["type"] == "code":
            tag = "programlisting"

            if block["language"]:
                if block["language"] == "plain":
                    output += "<informalexample><screen><![CDATA[\n"
                    tag = "screen"
                else:
                    output += "<informalexample><programlisting language=\"%s\"><![CDATA[\n" % block["language"];
            else:
                output += "<informalexample><programlisting><![CDATA[\n";

            for line in block["lines"]:
                output += ReplaceEntities(lines, symbol) + "\n"

            output += "]]></%s></informalexample>\n" % tag
        elif block["type"] == "markup":
            text = ExpandAbbreviations(symbol, block["text"])
            output += text + "\n"
        else:
            output += block["text"] + "\n"

    return output
