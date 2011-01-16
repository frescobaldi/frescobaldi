\version "2.13.43"
\include "bar_defaults.ily"
\layout {
  \context {
    \Score
    \override BarLine #'extra-offset = #'(-0.6 . 0)
  }
}
{ s \bar ".|" s }
