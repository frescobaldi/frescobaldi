=== Music View Preferences ===

Under *Music View* preferences you can configure how music is
displayed and printed.
This is where PDF files are displayed and all the settings
discussed here refer to PDF files only (SVG files have a
different viewer).

= Documents =

The *Documents* sections contains two main settings.

*Only load updated PDF documents*: if checked, when you
open a LilyPond source file you won't see the PDF document
in the viewer if it's not up-to-date (i.e. the PDF file is
older than the source file). If unchecked, PDF file will
be opened regardless.

*Remember View settings per-document*: if checked, every
document in the Music View will remember its own scale
and layout settings instead of the default ones (see
next section).

= Page scaling, layout and scrolling =

Here you can define the default scaling and layout of
the document. These preferences may be ignored for
the documents where different settings have been set,
if the option *Remember View settings per-document* is
checked.


= Printing Music =

The printing command is used to print a PostScript or PDF file.
On Linux you don't need this, but on Windows and macOS you can
provide a command to avoid that PDF documents are being printed
using raster images, which is less optimal.

`$pdf` gets replaced with the PDF filename, or alternatively,
`$ps` is replaced with the PostScript filename.
`$printer` is replaced with the printer's name to use.

Uncheck the *Use Frescobaldi's print dialog* option when the
printing command opens a print dialog itself, in which you can
select e.g. the page range to print and the printer to use.
If you don't use Frescobaldi's print dialog, you don't need to put
the `$printer` variable in your command line.

If Frescobaldi must fall back to printing using raster images,
you can specify the number of dots per inch here.
