\new GrandStaff <<
  \new Staff {
    \clef alto
    \key a \major
    e' f'8 \prall gis'-! a'16 r bes' r a4
  }
  \new PianoStaff <<
    \new Staff {
      \clef treble
      \key a \major
      <cis' e' a'>1
    }
    \new Staff {
      \clef bass
      \key a \major
      <a, a>1
    }
  >>
>>
