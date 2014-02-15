\version "2.18.0"
\include "breathe_defaults.ily"
\paper {
  top-markup-spacing = #
  '(
    (basic-distance . 1.8)
    (minimum-distance . 0)
    (padding . 0)
    (stretchability . 0)
   )
}

\markup \fill-line {
  \concat { \hspace #0.7 \musicglyph #"scripts.caesura.curved" }
}