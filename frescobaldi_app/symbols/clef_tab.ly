\version "2.18.0"
\include "clef_defaults.ily"

\paper {
  top-system-spacing = #
  '((basic-distance . 0)
    (minimum-distance . 4)
    (padding . 0))
}

\layout {
  \context {
    \TabStaff
    \remove "Time_signature_engraver"
    \override StaffSymbol.width = #4
    \override StaffSymbol.staff-space = #1
    \override Clef.font-size = #-3.5
  }
}
\new TabStaff { s4 }
