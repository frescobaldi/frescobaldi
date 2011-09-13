\version "2.14.0"
\include "glissando_defaults.ily"
\layout {
  \context {
    \Voice
    \override Glissando #'thickness = #1.5
  }
}
\makeGlissando #'dotted-line
