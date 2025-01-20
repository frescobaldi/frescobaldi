=== After engraving a score, the Music View does not show the music ===

1.  Does the `\score` block have a layout section?

    If a `\score` block has a `\midi` section but no `\layout` section,
    no PDF output is generated.
   
2.  Do you use an exotic way to specify the output filename?

    Frescobaldi is able to determine the output file names by looking at the
    document's filename and the various LilyPond commands that specify the
    output filename or -suffix.
    Frescobaldi even searches `\include` files for commands like
    `\bookOutputName` and `\bookOutputSuffix`.
    
    But if you use more complicated Scheme code in your document to specify the
    output filenames, Frescobaldi may not be able to correctly determine those
    filenames.
    In that case you can override the base name(s) using the [var_output
    `output`] document variable.


#SEEALSO
docvars
