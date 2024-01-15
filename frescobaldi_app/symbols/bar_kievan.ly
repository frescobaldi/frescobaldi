\version "2.18.0"
\include "bar_defaults.ily"
\paper {
  paper-height = 28\pt
  paper-width = 28\pt
  left-margin = 3\pt
  right-margin = 3\pt
}
\layout {
  \context {
    \Staff
    \override StaffSymbol.width = #1.44
  }
}

staffmarkup = \markup {
  \score {
    s
    \layout { }
  }
}
  
\markup \concat {
  \staffmarkup
  \musicglyph #"scripts.barline.kievan"
  \staffmarkup
}
