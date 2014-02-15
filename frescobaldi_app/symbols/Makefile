# Makefile

# Which LilyPond executable to use
LILYPOND=~/lilypond_bin/2.18.0-1/bin/lilypond

# Make .svg files from .ly files
lys = $(wildcard *.ly)
svgs = $(patsubst %.ly,%.svg,$(lys))

all: $(svgs)

$(svgs): %.svg: %.ly
	$(LILYPOND) -dbackend=svg -ddelete-intermediate-files $<

# Make some lilypond images also depend on the files they include
$(patsubst %.ly,%.svg,$(wildcard arpeggio_*.ly)): arpeggio_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard articulation_*.ly)): articulation_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard bar_*.ly)): bar_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard breathe_*.ly)): breathe_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard clef_*.ly)): clef_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard dynamic_*.ly)): dynamic_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard glissando_*.ly)): glissando_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard note_*.ly)): note_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard spanner_*.ly)): spanner_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard system_start_*.ly)): system_start_defaults.ily
$(patsubst %.ly,%.svg,$(wildcard time_*.ly)): time_defaults.ily

# Other dependencies
arpeggio_defaults.ily: icon_defaults.ily
articulation_defaults.ily: icon_defaults.ily
bar_defaults.ily: icon_defaults.ily
breathe_defaults.ily: icon_defaults.ily
clef_defaults.ily: icon_defaults.ily
dynamic_defaults.ily: icon_defaults.ily
glissando_defaults.ily: icon_defaults.ily
note_defaults.ily: icon_defaults.ily
spanner_defaults.ily: icon_defaults.ily
system_start_defaults.ily: icon_defaults.ily
time_defaults.ily: icon_defaults.ily

.PHONY: all
