\version "2.18.0"
\include "icon_defaults.ily"

\paper {
  paper-height = 22\pt
  paper-width = 22\pt
  left-margin = 1\pt
  right-margin = 1\pt
  top-system-spacing = #'
  ((basic-distance . 0)
   (minimum-distance . 2.3)
   (padding . 0)
   (stretchability . 0))
}

\layout {
  system-count = #1
  \context {
    \Score
    \override StaffSymbol.width = #'4
    \override StaffSymbol.thickness = #1.2
  }
  \context {
    \Staff
    \remove "Clef_engraver"
    \remove "Time_signature_engraver"
  }
}

makeBar = #
(define-music-function (parser location bar) (string?)
  #{
    s
    \alignGrob "Staff.BarLine" #'StaffSymbol #0 #0
    \bar $bar
    s
  #})

