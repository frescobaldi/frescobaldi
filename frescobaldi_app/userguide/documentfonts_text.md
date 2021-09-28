=== Text Fonts ===

== Browsing Text Fonts ==

The `Text Fonts` tab populates a list of all text fonts that are available to
LilyPond (which may differ from fonts seen by other programs). Each font may or
may not include subfamilies (such as *Condensed*, *Display* etc.) and eventually
one or mulitple weights, for which a short sample text is displayed.

Note that this list is created by running LilyPond with the
`-d-show-available-fonts` command line option, which may take some time. It is
possible that the tree view is initially empty until that process has finished.

Below the tree view is an entry field where a filter expression can be entered
that incrementally filters the list to quickly locate fonts. Searching is case
insensitive, and by default strings may be anywhere in the font name: the filter
`lib` will equally show `Liberation` and `Linux Libertine`. Filter expressions
support regular expressions, of which particularly the "border" characters are
of interest:

* *^*: Beginning of string: *^Lib* will now hide *Linux Libertine*
* *$*: End of string
* *\b*: word boundaries: *tu* will show *Century Schoolbook* and *Ubuntu Mono*
while *tu\b* will suppress the *Century*

== Selecting Text Fonts ==

A context menu in the tree view shows the three fonts currently selected as
*Roman*, *Sans* and *Typewriter* fonts. Clicking on any of the three menu items
will select the currently selected font for the corresponding font family and
trigger the {preview} to be updated.

=== Miscellaneous Font Information ===

The last tab lists some additional information about the font system, retrieved
from the *fontconfig* library. These too refer to the current LilyPond
installation and don't necessarily have to match the desktop environment's data.

#VARS

preview help documentfonts_preview
