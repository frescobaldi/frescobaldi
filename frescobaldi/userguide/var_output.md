=== The `output` document variable ===

Setting this variable suppresses the automatic output file name 
determination and makes Frescobaldi look for output documents (PDF, MIDI, 
etc.) with the specified basename, or comma-separated list of names.

If a name ends with a directory separator, output files are looked for in 
the specified directory.

All names are relative to the document's filename.

For example:

```lilypond
\version "2.14.2"
% -*- output: pdfs/;
\book {
  \bookOutputName #(string-append "pdfs/" some-variable)
  \score {
    \relative c' {
      c d e f g
    }
  }
}
```

You can set this variable if the automatic output file name determination 
would be time-consuming (as Frescobaldi parses the document and all the 
documents it includes, searching for the LilyPond commands that specify the 
output name, such as `\bookOutputName`, etc); or when the automatic output 
file name determination does not work due to complicated LilyPond code.

