%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% SCRIABIN		      %%%
%%% Piano Sonata No.10, Op.70 %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\include "lilypond-book-preamble.ly"

RH-A = \relative c'' {
  \time 9/16
  \set Score.currentBarNumber = #37
  \override Fingering.direction = #-1
  \override Slur.details.free-head-distance = #1
  \bar ""
  r8 a!32(\< -1 ^\markup \italic "lumineux et brillant" c
  e8.~\>\startTrillSpan
  \finger
        \markup
        \override #'(baseline-skip . 0)
        \column {
          \translate #'(1.5 . 1.5)
          \override #'(thickness . 2)
          \draw-line #'(1.25 . 0)
          "4523" }  8)\noBeam\!
  \override DynamicLineSpanner.Y-offset = #-5.5
  a,32(\<\stopTrillSpan c |
  e8.~\>\startTrillSpan 8)\noBeam\!
  a,32(\<\stopTrillSpan c e8.)\!
    -\tweak to-barline ##t \startTrillSpan \bar "||"
  \set Staff.timeSignatureFraction = 9/16
  \tempo "Allegro"
  \voiceOne
  \override Slur.details.free-head-distance = #2
  e8(\stopTrillSpan
    -5
    -\markup \italic "avec émotion"
  es16~ 8 e16 es d-5 des |
  c4.-5 ces8.) |
}

RH-B = \relative c'' {
  s8.*6 |
  \voiceTwo
  \repeat unfold 3 { r16 a( f) } |
  \repeat unfold 2 { r16 as( fes) } r8. |
}

LH-A = \relative c' {
  \time 9/16
  \clef bass
  r8.
  \voiceOne
  <a! c e g>4.-- |
  q-- q8.-- |
  \set Staff.timeSignatureFraction = 3/8
  \scaleDurations 3/2 {
  \oneVoice
  r8
  \override Fingering.direction = #-1
  \shape #'((0 . -1.5)(0 . -0.75)(0 . -0.75)(0 . -1.5))Slur
  a16[_(-1 c, f,-1 c]-3 as[ des as'-1 des]
    -\tweak extra-offset #'(0 . 2)-3
  as') r |
  }
}

LH-B = \relative c, {
  s8.*2/3
  \once \override Flag.stroke-style = #"grace"
  \magnifyMusic 0.75 {
  <c f c'>8.*1/3~ }
  \voiceTwo
  q4. |
  \override Rest.staff-position = #-2
  r r8. |
}

dyn = {
  s8.*6 |
  s8-\tweak Y-offset #-8 \p
}

\score {

\new PianoStaff
  <<
    \new Staff
    <<
      \new Voice { \RH-A }
      \new Voice { \RH-B }
    >>
    \new Dynamics \dyn
    \new Staff
    <<
      \new Voice { \LH-A }
      \new Voice { \LH-B }
    >>
  >>

  \layout {
    \context {
      \Staff
      \remove "Dot_column_engraver"
    }
    \context {
      \Voice
      \consists "Dot_column_engraver"
    }
  }
}
