=== Custom mode ===
    
The *Engrave (Custom)* dialog ({key_engrave_custom}) gives you detailed access
to all aspects of the LilyPond command.

You can configure a number of options through the graphical user interface and
then fine-tune the command line to be used for LilyPond directly.

You can select from the LilyPond versions defined in the [prefs_lilypond 
Preferences] dialog, from the output formats available to LilyPond and (for 
PNG output) from a number of image resolutions.

The options *Verbose Output* and *English Messages* may be relevant if you want
to send information to a mailing list, and *Delete Intermediate Output Files*
makes sure that LilyPond deletes e.g. PostScript files after they have been
converted to PDF.

Most of these settings are reflected in the Command Line text edit field.

The following replacements will be made:

!`$lilypond`
: The LilyPond executable

!`$include`
: All the include paths

!`$filename`
: The filename of the document



#VARS
key_engrave_custom shortcut engrave engrave_custom

