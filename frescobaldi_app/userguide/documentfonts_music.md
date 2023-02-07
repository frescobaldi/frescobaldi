=== Music Fonts ===

LilyPond can natively use alternative notation fonts since version `2.19.12`,
and version `2.18.2` can be patched with some (little) effort. However, notation
fonts have to be provided directly within each LilyPond installation. The
*Document Fonts* dialog can manage the installation of music fonts for each
LilyPond instance. *NOTE:* If LilyPond (not Frescobaldi) is installed in a
location that is not writable for Frescobaldi (typically when installed for all
users or from a Linux distribution package), Frescobaldi can currently not
perform this task. Please refer to {notationfontswiki} for more information on
LilyPond's music font handling.

Freely available notation fonts can be downloaded from {notationfonts}, but it
is recommended to also visit {mtf}, an online store with a collection of
extraordinary non-free music fonts.

== Browsing Music Fonts ==

The main area of the *Music Fonts* tab is a list with all music fonts found in
the current LilyPond installation. If no alternative music fonts are installed
for the current LilyPond instance, at least *Emmentaler* should be present in
the list. For each font checkboxes reveal whether font files are present in OTF,
SVG and WOFF format. Most fonts include a dedicated brace font but several
don't, and for these the default fallback is LilyPond's own *Emmentaler* font.

Selecting a row in the list will select the given font (and its *-brace* font if
available) as the current music font and trigger the {preview} to
be updated.

== Managing Music Fonts ==

Above the font list is a row with buttons to manage music font installation in
the current LilyPond instance.

= Local Font Repository =

If a directory is made known as a local repository for music fonts (see
{paths}) its content can easily be used as a source for font installation
in arbitrary numbers of LilyPond instances. The easiest way to make use of this
is to download or clone the font repository from GitHub ({notationfonts}) and
save it in this location.

= Installing Music Fonts =

Frescobaldi installs music fonts in a given LilyPond instance by creating
*symbolic links* from a source directory into the font directory within the
LilyPond installation. *NOTE:* If LilyPond is installed in a location that is
not writable for Frescobaldi these functions will fail (without doing any
damage).

If a Local Font Repository is defined all fonts from that repository can be
added to the current LilyPond installation by clicking on the *Install (repo)*
button. If the corresponding checkbox in the Preferences page is checked this
will be done upon *every* start of the dialog, which basically makes sure that
all installed LilyPond versions can be expected to have all music fonts
available.

Clicking the *Install...* button will open a directory chooser dialog, and the
selected directory will be recursively searched, installing all fonts found
there. This may be used for randomly downloaded music fonts. Note that the
original files have to remain in the location where they were at the time of
installation because otherwise the symbolic link would break.

= Removing Music Fonts =

The *Remove* button tries to remove the currently selected music font from the
LilyPond installation by removing the symbolic link from the LilyPond
installation directory. If the font files found are real files instead of
symbolic links (because the font has been installed externally) the removal
aborts with a message box in order to avoid lasting damage. Note that this is
always true for the *Emmentaler* font that ships with LilyPond itself.

#VARS

notationfonts url https://github.com/openlilylib-resources/lilypond-notation-fonts
notationfontswiki url https://github.com/openlilylib-resources/lilypond-notation-fonts/wiki
mtf url https://www.musictypefoundry.com
preview help documentfonts_preview
paths help prefs_paths
