=== (Generic) Import ===

Using {menu_import}, you can import any file that is compatible with the 
LilyPond import tools (musicxml2ly, midi2ly and abc2ly). For each tool and 
dialog see {musicxml}, {midi} and {abc}.

*Note that the specific importer is determined with the help of the file extension 
(.xml, .mxl, .midi, .mid or .abc) and without that the importer will fail.
If you get a file type error use the specific importer directly from the menu.*

#VARS
menu_import menu file -> &Import/Export -> Import...
musicxml help musicxml_import
midi help midi_import
abc help abc_import
