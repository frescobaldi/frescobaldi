\version "2.18.0"
\include "spanner_defaults.ily"

{
  \override Stem.length = #3
  \stemUp
  \teeny
  d''4\melisma e'' c''\melismaEnd
}
\addlyrics {
  \teeny
  \override VerticalAxisGroup.nonstaff-relatedstaff-spacing =
  #'((padding . -1.9)
     (basic-distance . -1.9)
     (minimum-distance . -1.9)
     (stretchability . 0))
  aa __
}
