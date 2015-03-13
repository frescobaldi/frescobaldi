\version "2.18.0"

\include "icon_defaults.ily"

\paper {
  paper-width = 13\pt
  paper-height = 13\pt
}

\markup {
  \combine
  \concat {
    \override #'(font-name . "Helvetica") "a"
    \translate #'(0.2 . 0.3) \override #'(font-name . "Courier Bold") \small "c"
  }
  \translate #'(1.1 . -1.3) \override #'(font-name . "Times Bold Italic") "b"
}
