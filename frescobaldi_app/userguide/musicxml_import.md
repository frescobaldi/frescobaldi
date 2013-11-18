=== Import Music XML ===

Using {menu}, you can import a Music XML file using the command line tool 
musicxml2ly from the LilyPond package.

In this dialog you can set some parameters for the musicxml2ly import.
Currently there are four parameters that can be set by the checkboxes:

!`--nd --no-articulation-directions`
: do not convert directions (^, _ or -) for articulations, dynamics, etc.

!`--nrp --no-rest-positions`
: do not convert exact vertical positions of rests

!`--npl --no-page-layout`
: do not convert the exact page layout and breaks

!`--no-beaming`
: do not convert beaming information, use LilyPonds automatic beaming instead.


The following replacements will be made in the command line:

!`$musicxml2ly`
: The musicxml2ly executable

!`$filename`
: The filename of the document


#VARS
menu menu file -> &Import -> Import MusicXML...
