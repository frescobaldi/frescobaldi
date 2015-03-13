\version "2.18.0"
\include "note_defaults.ily"

\paper {
  left-margin = #0.0
}
\markup \line {
  \combine
  \note #"4" #.8
  \lower #0.5 \halign #-2.4 \small \bold \char ##x2026
}
