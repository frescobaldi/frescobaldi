# MakeFile

all: _lilypond_data.py _scheme_data.py

# Set your LILYPOND environment variable before running make.
# export LILYPOND=/path/to/bin/lilypond
_lilypond_data.py: getdata.ly
	$(LILYPOND) -dno-print-pages $< > $@

_scheme_data.py: makeschemedata.py
	python makeschemedata.py
