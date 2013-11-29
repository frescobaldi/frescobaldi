=== Import Music XML ===

Using {menu_import}, you can import a Music XML file using the command line tool
`musicxml2ly` from the LilyPond package.

In this dialog there are two tabs. In the first you can set some parameters 
for the musicxml2ly import. In the second you can set some actions on the 
imported LilyPond source code.

Your settings in both tabs are remembered until the next time you use this dialog.

== The musicxml2ly tab ==

In this tab you have the following options:

 * Import articulation directions
 * Import rest positions
 * Import page layout
 * Import beaming
 * Pitches in absolute mode
 * Language for pitch names

The first four options are score elements you can retrieve from the 
musicXML-file if they are present and if you prefer not to use LilyPond's 
automatic handling of these elements.

The next two options can be used if you prefer to have the source code in 
absolute mode or if you prefer a different pitch name language than the 
default.

At the bottom you have a text area that mimics the command line text used to 
run `musicxml2ly`. If you are familiar with command line tools in general 
and musicxml2ly in particular you can edit this text directly, otherwise you 
can just ignore this.


== The *after import* tab ==

After `musicxml2ly` is run and the new ly-file is created you can set 
Frescobaldi to automatically do some adjustments on the new file.

Reformat source:
:  the code is reformatted.
   (This is identical to running Tools -> Format.)

Trim durations (Make implicit per line):
:  repeated time duration on the same line are deleted.
   (This is identical to running Tools -> Rhythm -> Make implicit per line.)

Remove fraction duration scaling:
:  if single notes, rests or chords are multiplied by a fraction `N/M` by
   appending `*N/M` this scaling is removed.
   (This can be useful to prevent unwanted scaling to emerge from ill-formatted
   musicXML-files.)

Engrave directly:
:  LilyPond runs directly.
   (This is identical to running LilyPond -> Engrave (preview).)


#VARS
menu_import menu file -> &Import -> Import MusicXML...
