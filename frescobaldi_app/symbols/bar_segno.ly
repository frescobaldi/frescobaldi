\version "2.13.43"
\include "bar_defaults.ily"
\paper {
  paper-height = 40\pt
  paper-width = 40\pt
  left-margin = 10\pt
  right-margin = 10\pt
}
\layout {
  \context {
    \Score
    \override BarLine #'extra-offset = #'(-1.2 . 0)
  }
}
{ s \bar "S" s }
