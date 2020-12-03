import unittest

from pgidocgen.debug import parse_lines, parse_compile_units


LINES = """\
CU: ../atk/atkvalue.c:
File name                            Line number    Starting address    View    Stmt
atkvalue.c                                   303             0x18090               x
atkvalue.c                                   420             0x18330               x

/usr/include/x86_64-linux-gnu/bits/string_fortified.h:
string_fortified.h                            59             0x18330       1       x
string_fortified.h                            71             0x18330       2       x
string_fortified.h                            71             0x18330       3

CU: ../atk/atkversion.c:
File name                            Line number    Starting address    View    Stmt
atkversion.c                                  53             0x18980               x

CU: ../atk/atkwindow.c:
File name                            Line number    Starting address    View    Stmt
atkwindow.c                                   66             0x189d0               x
"""

INFO = """\
 <0><b>: Abbrev Number: 1 (DW_TAG_compile_unit)
    <c>   DW_AT_producer    : (indirect string, offset: 0x14f7): GNU C99 8.3.0 -mtune=generic -march=x86-64 -g -O2 -std=c99 -fstack-protector-strong -fPIC -fvisibility=hidden
    <10>   DW_AT_language    : 12	(ANSI C99)
    <11>   DW_AT_name        : (indirect string, offset: 0x1eb5): atk/atk-enum-types.c
    <15>   DW_AT_comp_dir    : (indirect string, offset: 0xfed): ./obj-x86_64-linux-gnu
    <19>   DW_AT_low_pc      : 0xb770
    <21>   DW_AT_high_pc     : 0x676
    <29>   DW_AT_stmt_list   : 0x0
"""

LINES2 = """\
./gsf-input-memory.c:[++]
gsf-input-memory.c                            95             0x1fd2c       1       x
gsf-input-memory.c                            95             0x1fd2c       2
gsf-input-memory.c                            95             0x1fd3c
"""

INFO2 = """\
 <0><2037c>: Abbrev Number: 14 (DW_TAG_compile_unit)
    <2037d>   DW_AT_producer    : (indirect string, offset: 0xaeb): GNU C17 8.3.0 -mtune=generic -march=x86-64 -g -O2 -fstack-protector-strong -fPIC
    <20381>   DW_AT_language    : 12	(ANSI C99)
    <20382>   DW_AT_name        : (indirect string, offset: 0x7720): gsf-input-memory.c
    <20386>   DW_AT_comp_dir    : (indirect string, offset: 0x1211): ./gsf
    <2038a>   DW_AT_low_pc      : 0x1fb00
    <20392>   DW_AT_high_pc     : 1398
    <20394>   DW_AT_stmt_list   : 0xd5d1
"""


class TestDebug(unittest.TestCase):

    def test_parse_lines(self):
        cus = {
            '../atk/atkvalue.c': '../atk/atkvalue.c',
            '../atk/atkversion.c': '../atk/atkversion.c',
        }
        lines = parse_lines(LINES, cus)
        assert lines[0x18090] == ('../atk/atkvalue.c', '303')
        assert lines[0x18330] == ('../atk/atkvalue.c', '420')
        assert lines[0x18980] == ('../atk/atkversion.c', '53')

    def test_parse_lines2(self):
        cus = parse_compile_units(INFO2)
        lines = parse_lines(LINES2, cus)
        assert lines[0x1fd2c] == ('gsf/gsf-input-memory.c', '95')

    def test_parse_info(self):
        cu = parse_compile_units(INFO)
        assert cu["atk/atk-enum-types.c"] == "atk/atk-enum-types.c"
