\version "2.13.43"
\include "bar_defaults.ily"
\paper {
  top-system-spacing = #
  '((basic-distance . 0)
    (minimum-distance . 2.2)
    (padding . 0))
}
\layout {
  \context {
    \Score
    \override BarLine #'extra-offset = #'(-0.1 . -0.05)
  }
  \context {
    \Staff
    \override StaffSymbol #'staff-space = #(/ 7 8)
  }
}
{ s \bar "'" s }
