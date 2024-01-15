\version "2.18.0"

\include "icon_defaults.ily"

\paper {
  paper-height = 24\pt
  paper-width = 24\pt
  indent = #0
  left-margin = 2\pt
  top-system-spacing = #'
  (
   (basic-distance . 0)
   (minimum-distance . 2.4)
   (padding . 0)
   (stretchability . 0))
}

\layout {
  \context {
    \Staff
    \override StaffSymbol.transparent = ##t
    \override StaffSymbol.width = #4
    \remove "Clef_engraver"
    \remove "Time_signature_engraver"
  }
  \context {
    \Voice
    \override NoteHead.no-ledgers = ##t
    \override NoteHead.stencil = #empty-stencil
    \override Stem.stencil =#empty-stencil
  }
}

centerArpeggio = {
  \alignGrob #'(Staff Arpeggio) #'StaffSymbol #0 #0
}
