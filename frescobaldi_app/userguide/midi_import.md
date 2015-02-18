=== Import Midi ===

Using {menu_import}, you can import a Midi file using the command line tool
`midi2ly` from the LilyPond package.

In this dialog there are two tabs. In the first you can set some parameters 
for the midi2ly import. In the second you can set some actions on the 
imported LilyPond source code.

Your settings in both tabs are remembered until the next time you use this dialog.

== The midi2ly tab ==

In this tab you have the following options:

 * Pitches in absolute mode

This option can be used if you prefer to have the source code in 
absolute mode.

You can also change the LilyPond version to use.

At the bottom you have a text area that mimics the command line text used to 
run `midi2ly`. If you are familiar with command line tools in general 
and midi2ly in particular you can edit this text directly, otherwise you 
can just ignore this.


== The *after import* tab ==

After `midi2ly` is run and the new ly-file is created you can set 
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
menu_import menu file -> &Import -> Import Midi...
