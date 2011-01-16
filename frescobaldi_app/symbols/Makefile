# Makefile

# Which LilyPond executable to use
LILYPOND=~/lilypond_bin/2.13.43-1/bin/lilypond

# Make .svg files from .ly files
lys = $(wildcard *.ly)
svgs = $(patsubst %.ly,%.svg,$(lys))

all: $(svgs)

$(svgs): %.svg: %.ly
	$(LILYPOND) -dbackend=svg -ddelete-intermediate-files $<

# Make some lilypond images also depend on the files they include
$(patsubst %.ly,%.svg,$(wildcard note_*.ly)): note_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard articulation_*.ly)): articulation_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard clef_*.ly)): clef_defaults.ily

# Other dependencies
clef_defaults.ily: icon_defaults.ily
articulation_defaults.ily: icon_defaults.ily



.PHONY: all
