# Makefile that builds the MO files

# The python interpreter
PYTHON = python

potfile = frescobaldi.pot

pofiles = $(wildcard *.po)
mofiles = $(patsubst %.po,%.mo,$(pofiles))


all: $(mofiles)


$(pofiles): $(potfile)
	msgmerge -U $@ $<

$(potfile):
	$(PYTHON) update-pot.py

$(mofiles): %.mo: %.po
	msgfmt -o $@ $<
	$(PYTHON) molint.py $@
