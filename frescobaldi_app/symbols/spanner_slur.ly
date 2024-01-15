\version "2.18.0"

\include "spanner_defaults.ily"
\paper {
  left-margin = 2\pt
}
\layout {
  \context {
    \Voice
    \override Stem.length = #0
    \override Stem.direction = #DOWN
    \override Stem.transparent = ##t
    \override Tie.minimum-length = #3.6
    \override Tie.extra-offset = #'(0 . -.2)
    \override Tie.thickness = #2
    \override NoteHead.X-extent = #'(0 . 0)
    \override NoteHead.stencil = #empty-stencil
  }
}

{ a'~ a' }
