\version "2.13.43"
\include "clef_defaults.ily"

\layout {
  \context {
    \Staff
    \override OctavateEight
    #'extra-offset = #'(0.6 . 0.6)
  }
}

{ \clef "treble_8" s}
