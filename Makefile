all: build

build:
	sphinx-build -n . _build

show: build
	xdg-open ./_build/index.html

clean:
	rm -rf _build

.PHONY: clean show build
