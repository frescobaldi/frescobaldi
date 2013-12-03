=== LilyPond Preferences

Here you can configure how LilyPond is run when you engrave your document.

If you have multiple versions of LilyPond installed you can specify them 
here, and configure Frescobaldi to automatically choose the right one, based 
on the version number that is set in the document. See {link}.

If the LilyPond executable is not in your system's PATH you can specify the 
full path here so Frescobaldi can run it. For the helper applications like 
`convert-ly` and `lilypond-book` you don't need to specify the full path if 
they are in the same directory as the LilyPond executable itself.

You may enter a custom label to easily recognize a specific LilyPond instance.
I you do not enter a label, "LilyPond" is used.

You can also configure how LilyPond is run. See the tooltips of
the settings for more information.

Finally, you can specify a list of paths where the LilyPond `\include`
command looks for files. You can change the order of the includes by
dragging them inside the list. This influences the order in which LilyPond
searches for files.

#VARS
link help prefs_lilypond_autoversion
