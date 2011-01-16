\version "2.13.43"
\include "icon_defaults.ily"

\paper {
  paper-height = 22\pt
  paper-width = 22\pt
  left-margin = 1\pt
  right-margin = 1\pt
  
  top-system-spacing = #
  '((basic-distance . 0)
    (minimum-distance . 2.2)
    (padding . 0))

}

\layout {
  \context {
    \Score
    \override StaffSymbol #'width = #'4
  }
  \context {
    \Staff
    \remove "Clef_engraver"
    \remove "Time_signature_engraver"
  }
}
