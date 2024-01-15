\version "2.18.0"
\include "bar_defaults.ily"
\paper {
  paper-height = 40\pt
  paper-width = 40\pt
  left-margin = 2.5\pt
  right-margin = 2.5\pt
}
\layout {
  \context {
    \Staff
    \override StaffSymbol.width = #7
  }
}
{ \makeBar "S" }
