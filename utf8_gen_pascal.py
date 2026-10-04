#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (C) 2014-2026 Free Software Foundation, Inc.
# Copyright The GNU Toolchain Authors.
# This file is part of the GNU C Library.
#
# The GNU C Library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# The GNU C Library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with the GNU C Library; if not, see
# <https://www.gnu.org/licenses/>.

'''glibc/localedata/charmaps/UTF-8 file generator script

This script generates a glibc/localedata/charmaps/UTF-8 file
from Unicode data.

Usage: python3 utf8_gen.py UnicodeData.txt EastAsianWidth.txt

It will output UTF-8 file
'''

import argparse
import re
import unicode_utils

# Auxiliary tables for Hangul syllable names, see the Unicode 3.0 book,
# sections 3.11 and 4.4.

JAMO_INITIAL_SHORT_NAME = (
    'G', 'GG', 'N', 'D', 'DD', 'R', 'M', 'B', 'BB', 'S', 'SS', '', 'J', 'JJ',
    'C', 'K', 'T', 'P', 'H'
)

JAMO_MEDIAL_SHORT_NAME = (
    'A', 'AE', 'YA', 'YAE', 'EO', 'E', 'YEO', 'YE', 'O', 'WA', 'WAE', 'OE',
    'YO', 'U', 'WEO', 'WE', 'WI', 'YU', 'EU', 'YI', 'I'
)

JAMO_FINAL_SHORT_NAME = (
    '', 'G', 'GG', 'GS', 'N', 'NJ', 'NH', 'D', 'L', 'LG', 'LM', 'LB', 'LS',
    'LT', 'LP', 'LH', 'M', 'B', 'BS', 'S', 'SS', 'NG', 'J', 'C', 'K', 'T',
    'P', 'H'
)

def process_range(start, end, outfile, name):
    '''Writes a range of code points into the CHARMAP section of the
    output file

    '''
    if 'Hangul Syllable' in name:
        # from glibc/localedata/ChangeLog:
        #
        #  2000-09-24  Bruno Haible  <haible@clisp.cons.org>
        #  * charmaps/UTF-8: Expand <Hangul Syllable> and <Private Use> ranges,
        #  so they become printable and carry a width. Comment out surrogate
        #  ranges. Add a WIDTH table
        #
        # So we expand the Hangul Syllables here:
        for i in range(int(start, 16), int(end, 16)+1 ):
            index2, index3 = divmod(i - 0xaC00, 28)
            index1, index2 = divmod(index2, 21)
            hangul_syllable_name = 'HANGUL SYLLABLE ' \
                                   + JAMO_INITIAL_SHORT_NAME[index1] \
                                   + JAMO_MEDIAL_SHORT_NAME[index2] \
                                   + JAMO_FINAL_SHORT_NAME[index3]
            outfile.write('{:<11s} {:<12s} {:s}\n'.format(
                unicode_utils.ucs_symbol(i), convert_to_hex(i),
                hangul_syllable_name))
        return
    # UnicodeData.txt file has contains code point ranges like this:
    #
    # 3400;<CJK Ideograph Extension A, First>;Lo;0;L;;;;;N;;;;;
    # 4DB5;<CJK Ideograph Extension A, Last>;Lo;0;L;;;;;N;;;;;
    #
    # The glibc UTF-8 file splits ranges like these into shorter
    # ranges of 64 code points each:
    #
    # <U3400>..<U343F>     /xe3/x90/x80         <CJK Ideograph Extension A>
    # …
    # <U4D80>..<U4DB5>     /xe4/xb6/x80         <CJK Ideograph Extension A>
    for i in range(int(start, 16), int(end, 16), 64 ):
        if i > (int(end, 16)-64):
            outfile.write('{:s}..{:s} {:<12s} {:s}\n'.format(
                    unicode_utils.ucs_symbol(i),
                    unicode_utils.ucs_symbol(int(end,16)),
                    convert_to_hex(i),
                    name))
            break
        outfile.write('{:s}..{:s} {:<12s} {:s}\n'.format(
                unicode_utils.ucs_symbol(i),
                unicode_utils.ucs_symbol(i+63),
                convert_to_hex(i),
                name))

def process_charmap(flines, outfile):
    '''This function takes an array which contains *all* lines of
    of UnicodeData.txt and write lines to outfile as used in the

    CHARMAP
    …
    END CHARMAP

    section of the UTF-8 file in glibc/localedata/charmaps/UTF-8.

    Samples for input lines:

    0010;<control>;Cc;0;BN;;;;;N;DATA LINK ESCAPE;;;;
    3400;<CJK Ideograph Extension A, First>;Lo;0;L;;;;;N;;;;;
    4DB5;<CJK Ideograph Extension A, Last>;Lo;0;L;;;;;N;;;;;
    D800;<Non Private Use High Surrogate, First>;Cs;0;L;;;;;N;;;;;
    DB7F;<Non Private Use High Surrogate, Last>;Cs;0;L;;;;;N;;;;;
    100000;<Plane 16 Private Use, First>;Co;0;L;;;;;N;;;;;
    10FFFD;<Plane 16 Private Use, Last>;Co;0;L;;;;;N;;;;;

    Samples for output lines (Unicode-Value UTF-8-HEX Unicode-Char-Name):

    <U0010>     /x10 DATA LINK ESCAPE
    <U3400>..<U343F>     /xe3/x90/x80 <CJK Ideograph Extension A>
    %<UD800>     /xed/xa0/x80 <Non Private Use High Surrogate, First>
    %<UDB7F>     /xed/xad/xbf <Non Private Use High Surrogate, Last>
    <U0010FFC0>..<U0010FFFD>     /xf4/x8f/xbf/x80 <Plane 16 Private Use>

    '''
    fields_start = []
    for line in flines:
        fields = line.split(";")
         # Some characters have “<control>” as their name. We try to
         # use the “Unicode 1.0 Name” (10th field in
         # UnicodeData.txt) for them.
         #
         # The Characters U+0080, U+0081, U+0084 and U+0099 have
         # “<control>” as their name but do not even have aa
         # ”Unicode 1.0 Name”. We could write code to take their
         # alternate names from NameAliases.txt.
        if fields[1] == "<control>" and fields[10]:
            fields[1] = fields[10]
        # Handling code point ranges like:
        #
        # 3400;<CJK Ideograph Extension A, First>;Lo;0;L;;;;;N;;;;;
        # 4DB5;<CJK Ideograph Extension A, Last>;Lo;0;L;;;;;N;;;;;
        if fields[1].endswith(', First>') and not 'Surrogate,' in fields[1]:
            fields_start = fields
            continue
        if fields[1].endswith(', Last>') and not 'Surrogate,' in fields[1]:
            process_range(fields_start[0], fields[0],
                          outfile, fields[1][:-7]+'>')
            fields_start = []
            continue
        fields_start = []
        if 'Surrogate,' in fields[1]:
            # Comment out the surrogates in the UTF-8 file.
            # One could of course skip them completely but
            # the original UTF-8 file in glibc had them as
            # comments, so we keep these comment lines.
            outfile.write('%')
        outfile.write('{:<11s} {:<12s} {:s}\n'.format(
                unicode_utils.ucs_symbol(int(fields[0], 16)),
                convert_to_hex(int(fields[0], 16)),
                fields[1]))

def convert_to_hex(code_point):
    '''Converts a code point to a hexadecimal UTF-8 representation
    like /x**/x**/x**.'''
    # Getting UTF8 of Unicode characters.
    # In Python3, .encode('UTF-8') does not work for
    # surrogates. Therefore, we use this conversion table
    surrogates = {
        0xD800: '/xed/xa0/x80',
        0xDB7F: '/xed/xad/xbf',
        0xDB80: '/xed/xae/x80',
        0xDBFF: '/xed/xaf/xbf',
        0xDC00: '/xed/xb0/x80',
        0xDFFF: '/xed/xbf/xbf',
    }
    if code_point in surrogates:
        return surrogates[code_point]
    return ''.join([
        '/x{:02x}'.format(c) for c in chr(code_point).encode('UTF-8')
    ])

def write_header_charmap(outfile):
    '''Write the header on top of the CHARMAP section to the output file'''
    outfile.write("<code_set_name> UTF-8\n")
    outfile.write("<comment_char> %\n")
    outfile.write("<escape_char> /\n")
    outfile.write("<mb_cur_min> 1\n")
    outfile.write("<mb_cur_max> 6\n\n")
    outfile.write("% CHARMAP generated using utf8_gen.py\n")
    outfile.write("% alias ISO-10646/UTF-8\n")
    outfile.write("CHARMAP\n")

def write_header_width(outfile, unicode_version):
    '''Writes the header on top of the WIDTH section to the output file'''
    outfile.write('% Character width according to Unicode {:s}.\n'.format(unicode_version))
    outfile.write('% Width is determined by the following rules, in order of decreasing precedence:\n')
    outfile.write('% - U+00AD SOFT HYPHEN has width 1, as a special case for compatibility (https://archive.is/b5Ck).\n')
    outfile.write('% - U+115F HANGUL CHOSEONG FILLER has width 2.\n')
    outfile.write('%   This character stands in for an intentionally omitted leading consonant\n')
    outfile.write('%   in a Hangul syllable block; as such it must be assigned width 2 despite its lack\n')
    outfile.write('%   of visible display to ensure that the complete block has the correct width.\n')
    outfile.write('%   (See below for more information on Hangul syllables.)\n')
    outfile.write('% - Combining jungseong and jongseong Hangul jamo have width 0; generated from\n')
    outfile.write('%   "grep \'^[^;]*;[VT]\' HangulSyllableType.txt".\n')
    #outfile.write('%   One composed Hangul "syllable block" like 퓛 is made up of\n')
    outfile.write('%   One composed Hangul "syllable block" like ???error python??? is made up of\n')
    outfile.write('%   two to three individual component characters called "jamo".\n')
    outfile.write('%   The complete block must have total width 2;\n')
    outfile.write('%   to achieve this, we assign a width of 2 to leading "choseong" jamo,\n')
    outfile.write('%   and of 0 to medial vowel "jungseong" and trailing "jongseong" jamo.\n')
    outfile.write('% - Non-spacing and enclosing marks have width 0; generated from\n')
    outfile.write('%   "grep -E \'^[^;]*;[^;]*;(Mn|Me);\' UnicodeData.txt".\n')
    outfile.write('% - "Default_Ignorable_Code_Point"s have width 0; generated from\n')
    outfile.write('%   "grep \'^[^;]*;\\s*Default_Ignorable_Code_Point\' DerivedCoreProperties.txt".\n')
    outfile.write('% - Double-width characters have width 2; generated from\n')
    outfile.write('%   "grep \'^[^;]*;[WF]\' EastAsianWidth.txt".\n')
    outfile.write('% - Default width for all other characters is 1.\n')
    outfile.write("WIDTH\n")

def process_width(outfile, ulines, dlines, elines, klines):
    '''ulines are lines from UnicodeData.txt.
    elines are lines from EastAsianWidth.txt containing characters with width
    “W” or “F”.
    dlines are lines from DerivedCoreProperties.txt which contain
    characters with the property “Default_Ignorable_Code_Point”.
    klines are lines from HangulSyllableType.txt which contain characters
    with syllable type “V” or “T”.
    '''
    # Wide and fullwidth characters have width 1
    width_dict = {}
    for line in elines:
        fields = line.split(";")
        if not '..' in fields[0]:
            code_points = (fields[0], fields[0])
        else:
            code_points = fields[0].split("..")
        for key in range(int(code_points[0], 16),
                         int(code_points[1], 16)+1):
            width_dict[key] = 2

    # Nonspacing and enclosing marks have width 0
    for line in ulines:
        fields = line.split(";")
        if fields[4] == "NSM" or fields[2] in ("Me", "Mn"):
            width_dict[int(fields[0], 16)] = 0

    # Conjoining vowel and trailing jamo have width 0
    for line in klines:
        fields = line.split(";")
        if not '..' in fields[0]:
            code_points = (fields[0], fields[0])
        else:
            code_points = fields[0].split("..")
        for key in range(int(code_points[0], 16),
                         int(code_points[1], 16)+1):
            width_dict[key] = 0

    # “Default_Ignorable_Code_Point”s have width 0
    for line in dlines:
        fields = line.split(";")
        if not '..' in fields[0]:
            code_points = (fields[0], fields[0])
        else:
            code_points = fields[0].split("..")
        for key in range(int(code_points[0], 16),
                         int(code_points[1], 16)+1):
            width_dict[key] = 0 # default width is 1


    # Special case: U+00AD SOFT HYPHEN
    del width_dict[0x00AD]

    # Special case: U+115F HANGUL CHOSEONG FILLER
    width_dict[0x115F] = 2

    for key in list(range(0x3248, 0x3250)):
        # These are “A” which means we can decide whether to treat them
        # as “W” or “N” based on context:
        # http://www.unicode.org/mail-arch/unicode-ml/y2017-m08/0023.html
        # For us, “W” seems better.
        width_dict[key] = 2
    for key in list(range(0x4DC0, 0x4E00)):
        width_dict[key] = 2

    same_width_lists = []
    current_width_list = []
    for key in sorted(width_dict):
        if not current_width_list:
            current_width_list = [key]
        elif (key == current_width_list[-1] + 1
              and width_dict[key] == width_dict[current_width_list[0]]):
            current_width_list.append(key)
        else:
            same_width_lists.append(current_width_list)
            current_width_list = [key]
    if current_width_list:
        same_width_lists.append(current_width_list)

    for same_width_list in same_width_lists:
        if len(same_width_list) == 1:
            outfile.write('{:s}\t{:d}\n'.format(
                unicode_utils.ucs_symbol(same_width_list[0]),
                width_dict[same_width_list[0]]))
        else:
            outfile.write('{:s}...{:s}\t{:d}\n'.format(
                unicode_utils.ucs_symbol(same_width_list[0]),
                unicode_utils.ucs_symbol(same_width_list[-1]),
                width_dict[same_width_list[0]]))

def ucs_symbol_pascal(code_point):
    '''Return the UCS symbol string for a Unicode character.'''
    if code_point < 0x10000:
        return '${:04X}'.format(code_point)
    else:
        return '${:08X}'.format(code_point)

def process_width_pascal(outfile, ulines, dlines, elines, klines):
    '''ulines are lines from UnicodeData.txt.
    elines are lines from EastAsianWidth.txt containing characters with width
    “W” or “F”.
    dlines are lines from DerivedCoreProperties.txt which contain
    characters with the property “Default_Ignorable_Code_Point”.
    klines are lines from HangulSyllableType.txt which contain characters
    with syllable type “V” or “T”.
    '''
    # Wide and fullwidth characters have width 1
    width_dict = {}
    for line in elines:
        fields = line.split(";")
        if not '..' in fields[0]:
            code_points = (fields[0], fields[0])
        else:
            code_points = fields[0].split("..")
        for key in range(int(code_points[0], 16),
                         int(code_points[1], 16)+1):
            width_dict[key] = 2

    # Nonspacing and enclosing marks have width 0
    for line in ulines:
        fields = line.split(";")
        if fields[4] == "NSM" or fields[2] in ("Me", "Mn"):
            width_dict[int(fields[0], 16)] = 0

    # Conjoining vowel and trailing jamo have width 0
    for line in klines:
        fields = line.split(";")
        if not '..' in fields[0]:
            code_points = (fields[0], fields[0])
        else:
            code_points = fields[0].split("..")
        for key in range(int(code_points[0], 16),
                         int(code_points[1], 16)+1):
            width_dict[key] = 0

    # “Default_Ignorable_Code_Point”s have width 0
    for line in dlines:
        fields = line.split(";")
        if not '..' in fields[0]:
            code_points = (fields[0], fields[0])
        else:
            code_points = fields[0].split("..")
        for key in range(int(code_points[0], 16),
                         int(code_points[1], 16)+1):
            width_dict[key] = 0 # default width is 1


    # Special case: U+00AD SOFT HYPHEN
    del width_dict[0x00AD]

    # Special case: U+115F HANGUL CHOSEONG FILLER
    width_dict[0x115F] = 2

    for key in list(range(0x3248, 0x3250)):
        # These are “A” which means we can decide whether to treat them
        # as “W” or “N” based on context:
        # http://www.unicode.org/mail-arch/unicode-ml/y2017-m08/0023.html
        # For us, “W” seems better.
        width_dict[key] = 2
    for key in list(range(0x4DC0, 0x4E00)):
        width_dict[key] = 2

# **********************  OVERRIDE UNICODE VALUES. *****************************
#https://emonkak.pages.dev/articles/wcwidth/
#https://github.com/emonkak/locale-patchers

    # General Punctuation (U+2000..U+206f)
    # But, excluding following the code ranges:
    # - HYPHEN (U+2010)
    # - NON-BREAKING HYPHEN (U+2011)
    # - EN QUAD (U+2000) .. RIGHT-TO-LEFT MARK(U+200F)
    # - LINE SEPARATOR (U+2028) .. NARROW NO-BREAK SPACE(U+202F)
    # - MEDIUM MATHEMATICAL SPACE (U+205F) .. NOMINAL DIGIT SHAPES(U+206F)
    #{ 'code_start': 0x2012, 'code_end': 0x2027, 'width': 2 },
    for key in list(range(0x2012, 0x2027)):
        width_dict[key] = 2

    #{ 'code_start': 0x2030, 'code_end': 0x205E, 'width': 2 },
    for key in list(range(0x2030, 0x205E)):
        width_dict[key] = 2

    # Letterlike Symbols (U+2100..U+214F)
    # Number Forms (U+2150..U+218F)
    # Arrows (U+2190..U+21FF)
    # Mathematical Operators (U+2200..U+22FF)
    # Miscellaneous Technical (U+2300..U+23FF)
    #{ 'code_start': 0x2100, 'code_end': 0x23ff, 'width': 2 },
    for key in list(range(0x2100, 0x23ff)):
        width_dict[key] = 2

    # Enclosed Alphanumerics (U+2460..U+24FF)
    #{ 'code_start': 0x2460, 'code_end': 0x24ff, 'width': 2 },
    for key in list(range(0x2460, 0x24ff)):
        width_dict[key] = 2

    # Geometric Shapes (U+25A0..U+25FF)
    # Miscellaneous Symbols (U+2600..U+26FF)
    # Dingbats (U+2700..U+27BF)
    #{ 'code_start': 0x25a0, 'code_end': 0x27bf, 'width': 2 },
    for key in list(range(0x25a0, 0x27bf)):
        width_dict[key] = 2

    # Miscellaneous Symbols and Arrows (U+2B00..U+2BFF)
    #{ 'code_start': 0x2b00, 'code_end': 0x2bff, 'width': 2 },
    for key in list(range(0x2b00, 0x2bff)):
        width_dict[key] = 2

    # Enclosed CJK Letters and Months (U+3200..U+32FF)
    #{ 'code_start': 0x3200, 'code_end': 0x32ff, 'width': 2 },
    for key in list(range(0x3200, 0x32ff)):
        width_dict[key] = 2

    # Yijing Hexagram Symbols (U+4DC0..U+4DFF)
    #{ 'code_start': 0x4dc0, 'code_end': 0x4dff, 'width': 2 },
    for key in list(range(0x4dc0, 0x4dff)):
        width_dict[key] = 2

    # Private Use Area (U+E000..U+F8FF)
    #{ 'code_start': 0xe000, 'code_end': 0xf8ff, 'width': 2 },
    for key in list(range(0xe000, 0xf8ff)):
        width_dict[key] = 2

    # OBJECT REPLACEMENT CHARACTER (U+FFFC)
    # REPLACEMENT CHARACTER (U+FFFD)
    #{ 'code_start': 0xfffc, 'code_end': 0xfffd, 'width': 2 },
    for key in list(range(0xfffc, 0xfffd)):
        width_dict[key] = 2
    # Mahjong Tiles (U+1F000..U+1F02F)
    # Domino Tiles (U+1F030..U+1F09F)
    # Playing Cards (U+1F0A0..U+1F0FF)
    # Enclosed Alphanumeric Supplement (U+1F100..U+1F1FF)
    # Enclosed Ideographic Supplement (U+1F200..U+1F2FF)
    # Miscellaneous Symbols and Pictographs (U+1F300..U+1F5FF)
    # Emoticons (U+1F600..U+1F64F)
    # Ornamental Dingbats (U+1F650..U+1F67F)
    # Transport and Map Symbols (U+1F680..U+1F6FF)
    # Alchemical Symbols (U+1F700..U+1F77F)
    # Geometric Shapes Extended (U+1F780..U+1F7FF)
    # Supplemental Arrows-C (U+1F800..U+1F8FF)
    # Supplemental Symbols and Pictographs (U+1F900..U+1F9FF)
    # Chess Symbols (U+1FA00..U+1FA6F)
    # Symbols and Pictographs Extended-A (U+1FA70..U+1FAFF)
    # Symbols for Legacy Computing (U+1FB00..U+1FBFF)
    #{ 'code_start': 0x1f000, 'code_end': 0x1fbf9, 'width': 2 },
    for key in list(range(0x1f000, 0x1fbf9)):
        width_dict[key] = 2

    # Supplementary Private Use Area-A (U+F0000..U+FFFFF)
    # Supplementary Private Use Area-B (U+100000..U+10FFFF)
    #{ 'code_start': 0xf0000, 'code_end': 0x10FFFD, 'width': 2 },
    for key in list(range(0xf0000, 0x10fffd)):
        width_dict[key] = 2
        
#************************ END OVERRIDE UNICODE VALUES ***************************

    same_width_lists = []
    current_width_list = []
    for key in sorted(width_dict):
        if not current_width_list:
            current_width_list = [key]
        elif (key == current_width_list[-1] + 1
              and width_dict[key] == width_dict[current_width_list[0]]):
            current_width_list.append(key)
        else:
            same_width_lists.append(current_width_list)
            current_width_list = [key]
    if current_width_list:
        same_width_lists.append(current_width_list)

    outfile.write("  table:array[0..{:d}] of width_item=(\n".format(len(same_width_lists)-1));
    comma=' ';
    for same_width_list in same_width_lists:
        if len(same_width_list) == 1:
            outfile.write('  {:s}(rs:{:s};rl:{:d};cw:{:d}) //{:s}\t{:d}\n'.format(comma,
                ucs_symbol_pascal(same_width_list[0]),
                0,
                width_dict[same_width_list[0]],
                unicode_utils.ucs_symbol(same_width_list[0]),
                width_dict[same_width_list[0]]))
        else:
            outfile.write('  {:s}(rs:{:s};rl:{:d};cw:{:d}) //{:s}...{:s}\t{:d}\n'.format(comma,
                ucs_symbol_pascal(same_width_list[0]),
                same_width_list[-1] - same_width_list[0],
                width_dict[same_width_list[0]],
                unicode_utils.ucs_symbol(same_width_list[0]),
                unicode_utils.ucs_symbol(same_width_list[-1]),
                width_dict[same_width_list[0]]))
        comma=','

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description='''
        Generate a UTF-8 file from UnicodeData.txt, DerivedCoreProperties.txt, EastAsianWidth.txt, and HangulSyllableType.txt
        ''')
    PARSER.add_argument(
        '-u', '--unicode_data_file',
        nargs='?',
        type=str,
        default='UnicodeData.txt',
        help=('The UnicodeData.txt file to read, '
              + 'default: %(default)s'))
    PARSER.add_argument(
        '-d', '--derived_core_properties_file',
        nargs='?',
        type=str,
        default='DerivedCoreProperties.txt',
        help=('The DerivedCoreProperties.txt file to read, '
              + 'default: %(default)s'))
    PARSER.add_argument(
        '-e', '--east_asian_with_file',
        nargs='?',
        type=str,
        default='EastAsianWidth.txt',
        help=('The EastAsianWidth.txt file to read, '
              + 'default: %(default)s'))
    PARSER.add_argument(
        '-k', '--hangul_syllable_type_file',
        nargs='?',
        type=str,
        default='HangulSyllableType.txt',
        help=('The HangulSyllableType.txt file to read, '
              + 'default: %(default)s'))
    PARSER.add_argument(
        '--unicode_version',
        nargs='?',
        required=True,
        type=str,
        help='The Unicode version of the input files used.')
    ARGS = PARSER.parse_args()

    unicode_utils.fill_attributes(ARGS.unicode_data_file)
    with open(ARGS.unicode_data_file, mode='r') as UNIDATA_FILE:
        UNICODE_DATA_LINES = UNIDATA_FILE.readlines()
    with open(ARGS.derived_core_properties_file, mode='r') as DERIVED_CORE_PROPERTIES_FILE:
        DERIVED_CORE_PROPERTIES_LINES = []
        for LINE in DERIVED_CORE_PROPERTIES_FILE:
            # If characters which are from reserved ranges
            # (i.e. not yet assigned code points)
            # are added to the WIDTH section of the UTF-8 file, then
            # “make check” produces “Unknown Character” errors for
            # these code points because such unassigned code points
            # are not in the CHARMAP section of the UTF-8 file.
            #
            # Therefore, we skip all reserved code points.
            if re.match(r'.*<reserved-.+>', LINE):
                continue
            if re.match(r'^[^;]*;\s*Default_Ignorable_Code_Point', LINE):
                DERIVED_CORE_PROPERTIES_LINES.append(LINE.strip())
    with open(ARGS.east_asian_with_file, mode='r') as EAST_ASIAN_WIDTH_FILE:
        EAST_ASIAN_WIDTH_LINES = []
        for LINE in EAST_ASIAN_WIDTH_FILE:
            if re.match(r'.*<reserved-.+>', LINE):
                continue
            if re.match(r'^[^;]*;\s*[WF]', LINE):
                EAST_ASIAN_WIDTH_LINES.append(LINE.strip())
    with open(ARGS.hangul_syllable_type_file, mode='r') as HANGUL_SYLLABLE_TYPE_FILE:
        HANGUL_SYLLABLE_TYPE_LINES = []
        for LINE in HANGUL_SYLLABLE_TYPE_FILE:
            if re.match(r'.*<reserved-.+>', LINE):
                continue
            if re.match(r'^[^;]*;\s*[VT]', LINE):
                HANGUL_SYLLABLE_TYPE_LINES.append(LINE.strip())
    with open('UTF-8', mode='w') as OUTFILE:
        # Processing UnicodeData.txt and write CHARMAP to UTF-8 file
        write_header_charmap(OUTFILE)
        process_charmap(UNICODE_DATA_LINES, OUTFILE)
        OUTFILE.write("END CHARMAP\n\n")
        # Processing EastAsianWidth.txt and write WIDTH to UTF-8 file
        write_header_width(OUTFILE, ARGS.unicode_version)
        process_width(OUTFILE,
                      UNICODE_DATA_LINES,
                      DERIVED_CORE_PROPERTIES_LINES,
                      EAST_ASIAN_WIDTH_LINES,
                      HANGUL_SYLLABLE_TYPE_LINES)
        OUTFILE.write("END WIDTH\n")
        
    # Generate pascal include file wcwidth.inc    
    with open('wcwidth.inc', mode='w') as PASOUT:
        PASOUT.write("{ This file was generated by utf8_gen_pascal.py DO NOT EDIT\n")
        write_header_width(PASOUT, ARGS.unicode_version)
        PASOUT.write("}\n\n")
        PASOUT.write("type\n\n")
        PASOUT.write("  Pdata = ^width_item;\n")
        PASOUT.write("  width_item=record\n")
        PASOUT.write("    rs:uint32; //range start\n")
        PASOUT.write("    rl:uint32; //range length - 1.  rs+rl=last codepoint  \n")
        PASOUT.write("    cw:uint16; //char width\n")
        PASOUT.write("  end;\n\n")
        PASOUT.write("const\n\n")

        process_width_pascal(PASOUT,
                      UNICODE_DATA_LINES,
                      DERIVED_CORE_PROPERTIES_LINES,
                      EAST_ASIAN_WIDTH_LINES,
                      HANGUL_SYLLABLE_TYPE_LINES)
        PASOUT.write(");\n")
