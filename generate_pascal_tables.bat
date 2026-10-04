rem build pascal include file  wcwidth.inc

SET UNICODE_VERSION=18.0.0

rem delete prior versions

del UnicodeData.txt
del DerivedCoreProperties.txt
del EastAsianWidth.txt
del HangulSyllableType.txt
del wcwidth.inc
del UTF-8


wget http://www.unicode.org/Public/%UNICODE_VERSION%/ucd/UnicodeData.txt
wget http://www.unicode.org/Public/%UNICODE_VERSION%/ucd/DerivedCoreProperties.txt
wget http://www.unicode.org/Public/%UNICODE_VERSION%/ucd/EastAsianWidth.txt
wget http://www.unicode.org/Public/%UNICODE_VERSION%/ucd/HangulSyllableType.txt

python utf8_gen_pascal.py --unicode_version=%UNICODE_VERSION%

rem used for c language 
del UTF-8
