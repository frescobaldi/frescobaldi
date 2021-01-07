=== Document Fonts ===

The `Document Fonts` dialog which is accessible through {menu_dialog} provides
tools to browse available text fonts, to browse available music fonts and manage
their installation in a given LilyPond instance. It includes a configurable
font-setting command generator for use in LilyPond documents and provides a
intelligently cached preview to see and compare the impact of font settings on a
variety of provided sample scores, custom files and the “current document“.

The dialog is tied to the specific LilyPond installation that would be used for
a compilation (see {page_lilyversion}). All fonts are specific to that LilyPond
instance.

The dialog is split in two areas, a group of browsing and configuration tabs on
the left side and a preview pane on the right. In the left tabs text and music
fonts can be browsed and selected for use in a font-settings command. By
clicking on the `Copy` or `use` buttons the generated command can be copied to
the system clipboard or inserted in the current document (overwriting a
selection if present).

The selected fonts are remembered between Frescobaldi sessions, but by clicking
on the `Restore` button at the bottom of the dialog the selection can be reset
to LilyPond's default text and music fonts.

= Text Fonts =

The tab {page_textfonts} provides a searchable tree view of all text fonts
available to the current LilyPond installation. It also allows to select text
fonts for use in the score document.

= Music Fonts =

The tab {page_musicfonts} provides a list of available music fonts and a number
of controls to manage font installation in the current LilyPond installation.

= Font Command =

The tab {page_fontcommand} provides controls to configure the way how the
font-setting command is generated.

= Preview =

On the right side of the dialog a large area is reserved for a (cached) preview
of various scores using all combinations

#SUBDOCS
documentfonts_text
documentfonts_music
documentfonts_command
documentfonts_preview

#VARS
menu_dialog menu Tools -> Document Fonts...

page_lilyversion help prefs_lilypond
page_textfonts help documentfonts_text
page_musicfonts help documentfonts_music
page_fontcommand help documentfonts_command
