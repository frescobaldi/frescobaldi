\version "2.18.0"
\include "dynamic_defaults.ily"

\paper {
  top-markup-spacing = #'((basic-distance . 2.5))
}
\markup {
  \left-align
  \combine
  \draw-line #'(-4.8 . 1)
  \draw-line #'(-4.8 . -1)
}
