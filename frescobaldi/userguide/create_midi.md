=== How to generate a MIDI file? ===
    
By default, LilyPond creates only a PDF file of the music.
To create a MIDI file, you must wrap the music in a `\score` block and add a
`\midi` block to it.

For example:

```lilypond
\version "2.16.2"

music = \relative c' {
  c4 d e f g2
}

\score {
  \music
  \layout {}
  \midi {}
}
```

If you omit the `\layout` block, no PDF file will be generated, only a MIDI
file.

