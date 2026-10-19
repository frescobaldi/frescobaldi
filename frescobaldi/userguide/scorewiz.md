=== The Score Wizard ===
    
The Score Setup Wizard ({key}) in {menu} is designed
to quickly setup a LilyPond music score.

In the first tab, *Titles and Headers*, you can enter titling
information. The text you type is immediately displayed in
the preview on the left.

In the second tab, *Parts*, you can compose your score out of many
available part types.
Doubleclick a part type to add it to your score (or click Add).
Select the part in the score list to change some settings for the selected part,
if desired.
Many parts, especially Choir, have powerful options to set up the score the way
you want it.

In the third tab, *Score settings*, global score properties and
preferences can be set.

Click the Preview button to get a preview with some example music filled in.
Click OK to copy the generated LilyPond source text to the editor.

== Multiple pieces or movements ==

A special and powerful feature of the *Parts* tab is hidden in the 
"Containers" category in the part types list.

This category contains the Score, Book and Bookpart types, with which you
can setup a LilyPond document containing multiple scores or even books.
You may add Score, Bookpart or Book entries to the score view.
They can be nested: a Score can be added to a Bookpart or Book but you can't
add a Book to a Bookpart or a Score.

Then you can add musical parts.
If you want to create multiple scores with exact the same parts, you can just
add the parts to the top level of the score view, and then the scores, without
adding musical parts to the scores.
The scores will then use the parts in the top level of the score.

== Structuring pieces ==

You can use the "Structure" part type in the "Special" category to lay out
breaks, bar lines, and other structural elements separately from the music.
For example, to lay out a 16-bar section in lines of 4 bars, you can use:

```lilypond
structure = {
  \time 4/4
  \repeat unfold 4 {
    s1 * 4 |
    \break
  }
  \bar "||"
}
```

== Transposing instruments ==

The Score Wizard sets up all instrument parts for entry at their
sounding pitch. This has a number of practical advantages, like making
it easier to share parts between instruments. It is also logical
because transposition is a notation convention, not a property of the
instrument itself.

Transposition for such instruments is implemented in their part
definitions. For example, the definition for a B-flat trumpet part
may look like this:

```lilypond
trumpetBbPart = \new Staff \with {
  instrumentName = "Trumpet in Bb"
  shortInstrumentName = "Tr.Bb."
  midiInstrument = "trumpet"
} { \transposition bf \transpose bf c' \trumpetBb }
```

In this example, `\transpose bf c' \trumpetBb` changes a sounded B-flat
to a written C. But since `\transpose` affects both printed and MIDI
output, this results in an incorrect sounding pitch for the latter.
We therefore also use `\transposition bf` (which only affects MIDI) to
correct the sounding pitch back to B-flat.

== Customizing MIDI output ==

If "Place in a separate \score block" is checked on the *Score settings*
tab, the Score Wizard will create separate `\score` blocks for print
and MIDI output. Note the parts list is intentionally duplicated
between blocks rather than defined using a variable:

```lilypond
\score {
  <<
    \structurePart
    \flutePart
    \pianoPart
  >>
  \layout { }
}

\score {
  <<
    \structurePart
    \flutePart
    \pianoPart
  >>
  \midi { }
}
```

In this example, you could temporarily mute the flute part by commenting
its line in the MIDI `\score` while leaving it in print to avoid disrupting
the layout. A more advanced use might be to conserve MIDI channels in a
large orchestral score; you could combine all the MIDI parts for a particular
instrument while leaving them separate in print.

#VARS
key shortcut scorewiz scorewiz
menu menu file -> Score &Wizard...
