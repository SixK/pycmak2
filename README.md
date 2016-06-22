# pycmak2
A Python automatic C/C++ Makefile Generator

Simply call cmak2.py with a directory source name and you will get a Makefile containing all C/C++ files found in directory

pycmak2 is based on cmak perl script from Asher256 :
https://github.com/Asher256/cmak

cmak Perl Script has been ported to Python. 
Few functionnalities has been added like GCC optimizing flag parameter or addind callgraph support in makefile configuring compilation parameters to use Egypt.
http://www.gson.org/egypt/

This script has been tested for Morphos Amiga System, but not for Linux or Windows.
It may work straight without modifications, but some modifications might be necessary.

To manually install, copy cmak2.py /usr/bin/ then copy cmak2.cfg file to /usr/share/cmak/

Typical use (for Morphos):
cmak2.py src -dl
cmak2.py src/*.c -dl -e myProg
cmak2.py test.c -C -noixemul -LD -noixemul

SixK
