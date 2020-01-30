# Makefile that builds the MO files
#
# The strings from the application are in the frescobaldi.pot file,
# while the strings from the user guide are in the userguide.pot file.
# The MO files combine all the translations in one file per language.
#
# Usage:
#
#      make pot           # (re)create frescobaldi.pot and userguide.pot
#
#      make               # update all the po and mo files (target all)
#


# The python interpreter
PYTHON = python3

# directory where the MO files should go:
modir = ../frescobaldi_app/i18n

potfile = frescobaldi.pot
userguidepotfile = userguide.pot

# We want translation of the userguide to be optional.
# That's why we have two sets of PO files and two lists as LINGUAS files.
languages = $(shell cat frescobaldi/LINGUAS)
userguide_languages = $(shell cat userguide/LINGUAS)
pofiles = $(patsubst %,frescobaldi/%.po,$(languages))
userguidepofiles = $(patsubst %,userguide/%.po,$(userguide_languages))

mofiles = $(patsubst %,$(modir)/%.mo,$(languages))

all: mo

pot:
	$(PYTHON) ./update-pot.py

frescobaldi: $(pofiles)
userguide: $(userguidepofiles)
mo: $(mofiles)

$(pofiles): $(potfile)
	-msgmerge -U $@ $<
	sed -i '/^#: /{ s, ../, ../../,g; s, messages, ../messages,g;}' $@

$(userguidepofiles): $(userguidepotfile)
	-msgmerge -U $@ $<
	sed -i '/^#: /{ s, ../, ../../,g; s, messages, ../messages,g;}' $@

# one MO file is created from both the frescobaldi/LL.po and userguide/LL.po
$(mofiles): $(modir)/%.mo: frescobaldi/%.po userguide/%.po
	msgcat -o - $^ | msgfmt -o $@ -
	$(PYTHON) molint.py $@

