\version "2.18.0"
#(set-global-staff-size 10)
\include "icon_defaults.ily"
\paper {
  paper-height = 40\pt
  paper-width = 40\pt
  top-system-spacing = #'(
    (basic-distance . 3.9)
    (minimum-distance . 3.9)
    (padding . 0)
    (stretchability . 0))
}

\layout {
  indent = 7.5\pt
  system-count = #1
  \context {
    \Staff
    \remove "Clef_engraver"
    \remove "Time_signature_engraver"
    \override StaffSymbol.width = #14
  }
  \context {
    \Score
    \override StaffGrouper.staff-staff-spacing = #'(
      (basic-distance . 8)
      (minimum-distance . 8)
      (padding . 0)
      (stretchability . 8))
  }
}

music = <<
  \new Staff s4
  \new Staff s4
>>
