SOURCE=logo.svg
DEST=../../pgidocgen/gen/data/index/favicon.ico

all: $(DEST)

logo-16.png: $(SOURCE)
	inkscape $(SOURCE) --export-png $@ -w 16 -h 16

logo-24.png: $(SOURCE)
	inkscape $(SOURCE) --export-png $@ -w 24 -h 24

logo-32.png: $(SOURCE)
	inkscape $(SOURCE) --export-png $@ -w 32 -h 32

logo-48.png: $(SOURCE)
	inkscape $(SOURCE) --export-png $@ -w 48 -h 48

logo-64.png: $(SOURCE)
	inkscape $(SOURCE) --export-png $@ -w 64 -h 64

$(DEST): logo-16.png logo-24.png logo-32.png logo-48.png logo-64.png
	convert logo-16.png logo-24.png logo-32.png logo-48.png logo-64.png $(DEST)
	rm logo-16.png logo-24.png logo-32.png logo-48.png logo-64.png

.PHONY: clean

clean:
	rm -f logo-16.png logo-24.png logo-32.png logo-48.png logo-64.png favicon.ico
