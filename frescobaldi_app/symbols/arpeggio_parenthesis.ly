\version "2.14.0"
\include "arpeggio_defaults.ily"
\relative c' {
  \arpeggioParenthesis
  \override Staff.Arpeggio #'X-offset = #1.7
  <e f'>4\arpeggio
}
