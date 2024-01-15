\version "2.18.0"
\include "bar_defaults.ily"
\paper {
  top-system-spacing = #
  '((basic-distance . 0)
    (minimum-distance . 2.25)
    (padding . 0))
}
\layout {
  \context {
    \Staff
    \override StaffSymbol.staff-space = #(/ 7 8)
  }
}
{ \makeBar "'" }
