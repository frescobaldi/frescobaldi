=== Helper Applications ===
    
In this page you can enter commands to open different file types.
`$f` is replaced with the filename,
`$u` with the URL. 
Leave a field empty to use the operating system default application.

For the e-mail setting, the command should accept a 
`mailto:` url.

For the command prompt, the command should open a console window.
A `$f` value is replaced with the directory of the current document.

== Printing Music ==

The printing command is used to print a PostScript or PDF file.
On Linux you don't need this, but on Windows and Mac OS X you can
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
