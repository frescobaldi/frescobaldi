=== Engraving Scores ===

To engrave a score, Frescobaldi runs LilyPond with the correct commandline
options. There are four modes Frescobaldi can compile scores in:
*Preview*, *Publish*, *Layout Control* and *Custom*.

The *Preview mode* renders the PDF with point and click information enabled, so
that there is two-way navigation between the music view and the LilyPond source.

The *Publish mode* is used to produce the final PDF intented to be shared.

The *Layout Control mode* can be used to enable specific features that can help
in controlling and fine-tuning the layout of a score.

The *Custom mode* opens a dialog allowing you to specify the LilyPond command
in detail. This dialog also has options to let LilyPond engrave a score to
PostScript, SVG or PNG images, or to a PDF using the EPS backend.

All commands to run LilyPond can be found in the *LilyPond* menu. And if you
enable the *Automatic engrave* option, Frescobaldi will run LilyPond
automatically everytime the document is modified (in preview mode).

#SUBDOCS
engrave_preview
engrave_publish
engrave_layout
engrave_custom

#SUBDOCS_TODO
engrave_automatic
engrave_partial

