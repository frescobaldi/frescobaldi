=== Font Settings Command ===

In LilyPond music and text fonts are selected by issuing specific commands, and
on the *Font Command* tab the way this command is generated can be configured.
Choices made in this tab are remembered throughout Frescobaldi sessions. They
are immediately reflrected in the command preview and trigger an update of the
score preview. The content of the command preview will be copied to the
clipboard or inserted in the current document upon clicking on the respective
buttons.

== Considered Text Fonts ==

Three checkboxes regulate whether roman, sans, and typewriter fonts are
considered in the font-settings command. For each family that is *not* checked
LilyPond will use the default fonts.

== Command generation style ==

Frescobaldi can apply several styles of generating the font commands, which can
be selected by choosing from the different tabs in the lower part of the dialog.

= Traditional Style =

In the traditional style of setting fonts inside a *\paper* block arbitrary
fonts may be set or not, including the *music* font. So in addition to the three
text font families is is possible to selectively set the music font as well.

It is possible to generate a complete *\paper* block or not, depending on where
the generated command should be used.

= openLilyLib Style

{openlilylib} has a *notation-fonts* package with advanced functionality to load
notation fonts (together with text fonts) which Fresocbaldi makes available too.
With the openLilyLib approach notation fonts are *always* loaded, therefore the
"music" font selection can not be unchecked.

*NOTE:* In order for this to work the two openLilyLib packages `oll-core` and
`notation-fonts` have to be installed and available.

* *Load openLilyLib*:
This should be unchecked if *oll-core* is already loaded/included elsewhere in
the score files
* *Load notation-fonts package*:
The same consideration regarding the *notation-fonts* package.
* *Load font extensions:* Some fonts include additional glyphs beyond the
  regular LilyPond coverage. openLilylib provides stylesheets with supporting
  functions making the additional features available as commands or e.g.
  articulations. If this option is checked font extensions are loaded if
  available (otherwise nothing will happen).
* *Font stylesheets:* openLilyLib provides default stylesheets for each
  supported font, adjusting the visual appearance (e.g. line thickness of
  various score items) to match the characteristics of the given font. By
  default these are loaded automatically by the font command *\useNotationFont*.
  However, in some cases it may be necessary to *not* use the default stylesheet
  (e.g. for better integration with the project's "include" strategy) or to
  provide a custom stylesheet, which has to be the name of a file that LilyPond
  can find.


#VARS

openlilylib url https://github.com/openlilylib
