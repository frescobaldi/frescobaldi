=== Auto-completion ===

If not disabled in the {menu_tools} menu Frescobaldi assists the user with
auto-completion suggestions. As soon as two characters are entered in a
“word” a list with matching completions is collected, both from a list of
valid LilyPond terms (trying to only suggest words that are suitable in the
current context) and from parsing the current document.

{image_auto_complete_one}

If there is an ambiguous partial match it is automatically added and selected:

{image_auto_complete_two}

Hitting the TAB key will accept the partial completion and select the next
item in the dropdown box with suggestions. Holding down the Ctrl key causes
the dropdown elements to by cycled backwards.

{image_auto_complete_three_b}

Alternatively entering another character will also accept the partial suggestion
but add the new character afterwards. If that allows another partial completion
it will automatically be triggered:

{image_auto_complete_three}

At any point hitting ENTER will accept the currently highlighted entry from the
dropdown box. Note that matching is performed case insensitively while upon
accept the properly capitalized entry is inserted, replacing what has already
been entered.

Entering `.` (a dot) will also accept the highlighted entry and add the dot,
which is handy to enter grob properties.

{image_auto_complete_four}

#VARS
menu_tools menu tools

image_auto_complete_one image auto_complete_one.png
image_auto_complete_two image auto_complete_two.png
image_auto_complete_three image auto_complete_three.png
image_auto_complete_three_b image auto_complete_three1.png
image_auto_complete_four image auto_complete_four.png
