=== The Score Wizard ===
    
The Score Setup Wizard ({key}) in {menu} is designed
to quickly setup a LilyPond music score.

In the first tab, *Titles and Headers*, you can enter titling
information.

In the second tab, *Parts*, you can compose your score out of many
available part types.
Doubleclick a part type to add it to your score (or click Add).
Select the part in the score list to change some settings for the selected part,
if desired.
Many parts, especially Choir, have powerful options to set up the score the way
you want it.

In the third tab, *Score settings*, global score properties and
preferences can be set.

Click the Preview button to get a preview with some example music filled in.
Click OK to copy the generated LilyPond source text to the editor.

== Multiple pieces or movements ==

A special and powerful feature of the *Parts* tab is hidden in the 
"Containers" category in the part types list.

This category contains the Score, Book and Bookpart types, with which you
can setup a LilyPond document containing multiple scores or even books.
You may add Score, Bookpart or Book entries to the score view.
They can be nested: a Score can be added to a Bookpart or Book but you can't
add a Book to a Bookpart or a Score.

Then you can add musical parts.
If you want to create multiple scores with exact the same parts, you can just
add the parts to the top level of the score view, and then the scores, without
adding musical parts to the scores.
The scores will then use the parts in the top level of the score.

#VARS
key shortcut scorewiz scorewiz
menu menu file -> Score &Wizard...
