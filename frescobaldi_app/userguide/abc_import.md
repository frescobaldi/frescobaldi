=== Import ABC ===

Using {menu_import}, you can import an abc file using the command line tool
`abc2ly` from the LilyPond package.

Abc is a notation standard which like LilyPond is designed to notate music in 
plain text. It was designed primarily for folk and traditional tunes of Western 
European origin. 

In this dialog there are two tabs. In the first you can set some parameters 
for the abc2ly import. In the second you can set some actions on the 
imported LilyPond source code.

Your settings in both tabs are remembered until the next time you use this dialog.

== The abc2ly tab ==

In this tab you have the following options:

 * Import beaming

This option can be used to retain the beaming from the abc notation.

You can also change the LilyPond version to use.

At the bottom you have a text area that mimics the command line text used to 
run `abc2ly`. If you are familiar with command line tools in general 
and abc2ly in particular you can edit this text directly, otherwise you 
can just ignore this.


== The *after import* tab ==

After `abc2ly` is run and the new ly-file is created you can set 
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
menu_import menu file -> &Import -> Import abc...
