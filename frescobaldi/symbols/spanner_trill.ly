\version "2.18.0"
\include "spanner_defaults.ily"

\paper {
  top-markup-spacing = #
  '((basic-distance . 3)
    (minimum-distance . 0)
    (padding . 0)
    (stretchability . 0))
}

\markup {
  \fontsize #0
  \translate #'(1.3 . 0)
  \concat {
    \musicglyph #"scripts.trill"
    \musicglyph #"scripts.trill_element"
    \musicglyph #"scripts.trill_element"
  }
}
