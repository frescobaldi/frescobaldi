\version "2.14.0"

\include "icon_defaults.ily"

\paper {
  paper-height = 24\pt
  paper-width = 24\pt
  indent = #0
  left-margin = 2\pt
  top-system-spacing = #
  '(
    (padding . 0)
    (basic-distance . 0)
    (minimum-distance . 2.4)
   )
  last-bottom-spacing = #
  '(
    (basic-distance . 0)
    (padding . 0)
   )
}

\layout {
  \context {
    \Staff
    \override StaffSymbol #'transparent = ##t
    \override StaffSymbol #'width = #4
    \remove "Clef_engraver"
    \remove "Time_signature_engraver"
    \override Arpeggio #'X-offset = #1
  }
  \context {
    \Voice
    \override NoteHead #'no-ledgers = ##t
    \override NoteHead #'stencil = #empty-stencil
    \override Stem #'stencil =#empty-stencil
  }
}
