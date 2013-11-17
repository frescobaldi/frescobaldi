=== Lyrics ===
    
Frescobaldi can automatically place hyphens '{hyphen}' inside texts to make
those texts usable as lyrics.
It can use hyphenation dictionaries of OpenOffice.org, Scribus, etc.

To use this feature you must first select the text you want to hyphenate. Then
press {key_hyphen} or choose {menu_hyphen}.
In the dialog that appears, select the language.
Click OK or press Enter to have the hyphenation take place. 

A small limitation is that word processor hyphenation dictionaries often don't
want to break a word right after the first letter (e.g. '{example}'), because that
does not look nice in word processor texts. So it can happen that you
have to add some hyphens after the first letter of such lyrics. 

There is also a command to remove hyphenation. This can be useful if you have a
stanza of lyrics that you just want to display as a markup below the music.
Under {menu_settings} you can enter a list of directories to search for
hyphenation pattern files.

#VARS
hyphen md ` -- `
example md `a -- men`
key_hyphen shortcut lyrics lyrics_hyphenate
menu_hyphen menu tools -> submenu title|&Lyrics -> &Hyphenate Lyrics Text...
menu_settings menu edit -> Pr&eferences... -> Paths


