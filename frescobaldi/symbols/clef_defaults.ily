\version "2.18.0"

\include "icon_defaults.ily"

\paper {
  paper-height = 40\pt
  paper-width = 40\pt
  left-margin = 10\pt
  right-margin = 10\pt
  top-system-spacing = #'
  ((basic-distance . 0)
   (minimum-distance . 4)
   (padding . 0)
   (stretchability . 0))
}

\layout {
  indent = #0
  \context {
    \Staff
    \remove "Time_signature_engraver"
    \override StaffSymbol.width = #4
  }
}
