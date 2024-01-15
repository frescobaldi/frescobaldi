\version "2.18.0"

\include "icon_defaults.ily"

\paper {
  paper-width = 22\pt
  paper-height = 22\pt
  top-system-spacing = #
  '((basic-distance . 2.2)
    (minimum-distance . 0)
    (padding . 0)
    (stretchability . 0))
}

\layout {
  \context {
    \Staff
    \remove "Clef_engraver"
    \remove "Time_signature_engraver"
    \override StaffSymbol.width = #4.4
    \override StaffSymbol.transparent = ##t
  }
}
