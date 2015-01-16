=== Mode shift ===

Use the mode shifter to change all or selected notes to a specified mode or scale.

E.g. when shifting to the d (harmonic) minor scale, you would enter: 


```lilypond
d Minor
```

The supported modes are:

Major

Minor (harmonic)

Natminor (natural)

Dorian

(The capital letters are optional.)

The mode name should be preceded by a note name in the language of the document.

*Note that unlike the modal transposer all pitches will be shifted to the chosen 
scale regardless of which mode they possibly belonged to originally.*

This feature is currently experimental, see {experimental}.

#SEEALSO
modal_transpose

#VARS
experimental help experimental_features
