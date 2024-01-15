\version "2.18.0"

\include "icon_defaults.ily"
\paper {
  paper-height = 22\pt
  paper-width = 22\pt
  left-margin = 1\pt
  right-margin = 1\pt
  top-system-spacing = #
  '((minimum-distance . 0)
    (padding . 0)
    (basic-distance . 2.2)
    (stretchability . 0))
  
}

\layout {
  indent = #0
  \context {
    \Staff
    \remove "Clef_engraver"
    \remove "Time_signature_engraver"
    \override StaffSymbol.transparent = ##t
    \override StaffSymbol.width = #4
  }
  \context {
    \Voice
    \override NoteHead.stencil = #empty-stencil
    \override Stem.stencil = #empty-stencil
    \override Stem.length = #0
    \override Glissando.bound-details = #
  '((right
     (attach-dir . 0)
     (padding . 0)
     (Y . 2)
     (X . 4))
    (left
     (attach-dir . 0)
     (padding . 0)
     (X . 0)
     (Y . -2)))
  }
}

makeGlissando = #
(define-music-function (parser location style) (symbol?)
  #{
    \relative c'' {
      \override Glissando.style = $style
      b\glissando b
    }
  #})

