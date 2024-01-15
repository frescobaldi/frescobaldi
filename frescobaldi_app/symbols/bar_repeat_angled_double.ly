\version "2.18.0"
\include "bar_defaults.ily"
\paper {
  paper-height = 34\pt
  paper-width = 34\pt
  left-margin = 3\pt
  right-margin = 3\pt
}
\layout {
  \context {
    \Staff
    \override StaffSymbol.width = #5.5
  }
}
{ \makeBar ":|][|:" }
