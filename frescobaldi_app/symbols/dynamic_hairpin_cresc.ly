\version "2.14.0"
\include "dynamic_defaults.ily"

\paper {
  top-markup-spacing = #'((basic-distance . 2.5))
}

\markup {
  \combine
  \draw-line #'(4.8 . 1)
  \draw-line #'(4.8 . -1)
}
