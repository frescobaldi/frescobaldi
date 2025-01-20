=== Transpose ===
    
When transposing music, two absolute pitches need to be given to specify
the distance to transpose over. The pitches may include octave marks.
The pitches must be entered in the pitch name language used in the document.

The music will then be transposed from the first pitch to the second,
just as the `\transpose` LilyPond command would do.

E.g. when transposing a minor third upwards, you would enter:

```lilypond
c es
```

To transpose down a major second, you can enter:

```lilypond
c bes,
```

or:

```lilypond
d c
```

It is also possible to use the transpose function to change a piece of music
from C-sharp to D-flat, or to specify quarter tones if supported in the
pitch name language that is used.

The transpose function can transpose both relative and absolute music,
correctly handling key signatures, chordmode and octave checks.

