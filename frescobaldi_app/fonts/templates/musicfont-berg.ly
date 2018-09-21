\version "2.19.3"


\layout {
  \context {
    \Score
    \remove "Bar_number_engraver"
  }
}

global = {
  \key c \major
  \time 4/4
  \override Score.NonMusicalPaperColumn.line-break-permission = ##f
}

fffEspress = \markup { \dynamic fff \italic espress. }

clarinet = \relative b {
  \global
  \transposition bes
  \tempo "Ganz langsam." 4=40-44
  \repeat tremolo 8 { b32\mf ( \startTrillSpan ais) }
    \grace { c32[( \stopTrillSpan a] }
    \tuplet 3/2 {
      \repeat tremolo 16 gis64)
        _\markup "quasi Flatterzunge"
      \repeat tremolo 16 g
      \repeat tremolo 16 fis
    } |

  % 07
  r4
    \once \override DynamicText.X-offset = -4
    a32(\f\< cis f as c es g b
    e8 \staccatissimo )\sfz \breathe
    e8--\ff(_\markup \italic (schwungvoll)
    \acciaccatura b8 dis-- e--)

}

rightOne = \relative bes'' {
  \global
  % Music follows here.
  s2
  \voiceOne
  r8^\markup \italic "r.H."
  bes8--(_\fffEspress a4-- ~ |

  % 07
  a16 b fis \acciaccatura
  % TODO: This isn't an acciaccatura, but should rather be
  % a slashed grace plus tie
    {
      \stemDown d32
      \stemUp
    } d16
    \tuplet 6/4 {
      c16 bes g fis) f^>_. e^>_.
    }
    gis8->_( a4) gis8
}

rightTwo = \relative e' {
  \global
  % Music follows here.
  r8 <e ges bes d>4^(^\markup \italic "(voll)"
    ^\markup \italic "(Zeit lassen)"
    \arpeggio
      <d f a cis>8\arpeggio
      <b c es g b>2)\arpeggio

  % 07
  \set tieWaitForNote = ##t
  \voiceTwo
  b'16\rest \grace { c32[ ~ e] ~ } <c e>16
  b16\rest b
  \once \override TupletBracket.stencil = ##f
  \once \override TupletNumber.stencil = ##f
  \tuplet 3/2 {
    g16\rest bes \pp g
  }
  r8\<
  s2\!_\markup \italic cresc.
}

middle = \relative es'' {
  r8
    \once \override DynamicText.X-offset = -4
    es4->^\ff_(^\markup \italic marc.
    e8-> bes'->) r8 r4 |

  %07
  \stopStaff
}

left = \relative as, {
  \global
  % Music follows here.
  r8 <as g'>4_(^\markup \italic "l.H. übergreifen"\arpeggio
    <g fis'>8\arpeggio
    <fis e'>4.) ~ \sustainOn
    \tuplet 3/2 { q16 <f' g>-> <as, bes>->\sustainOff } |

 % 07
 es8->(\sustainOn <e' gis>4--)
   \once \override DynamicText.X-offset = -4
   des,8\f->(\sustainOff\sustainOn <d' ais' b>4--)
   bes,8->(\sustainOff\sustainOn <des' f a c>)
}

clarinetPart = \new Staff \clarinet

pianoPart = \new PianoStaff <<
  \new Staff = "right" << \rightOne
                          \rightTwo >>
  \new Staff = "middle" { \clef treble \middle }
  \new Staff = "left" { \clef bass \left }
>>

\score {
  <<
    \clarinetPart
    \pianoPart
  >>
  \layout {
    \context {
      \Score
      \accidentalStyle dodecaphonic-no-repeat
    }
  }
}
