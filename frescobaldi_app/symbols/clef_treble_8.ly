\version "2.18.0"
\include "clef_defaults.ily"

\layout {
  \context {
    \Staff
    \override ClefModifier.extra-offset = #'(0.6 . 0.6)
  }
}

{ \clef "treble_8" s}
