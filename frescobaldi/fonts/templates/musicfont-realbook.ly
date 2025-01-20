\include "lilypond-book-preamble.ly"

title = "The Quick Brown Fox"
composer = "-Moser"
meter = "(Uptempo ballad)"

realBookTitle = \markup {
  \score {
    {
      \override TextScript.extra-offset = #'(0 . -4.5)
      s4
      s^\markup {
        \fill-line {
          \fontsize #1 \lower #1 \rotate #7 \concat { " " #meter }
          \fontsize #8
          \override #'(offset . 7)
          \override #'(thickness . 6)
          \underline \sans #title
          \fontsize #1 \lower #1 \concat { #composer " " }
        }
      }
      s
    }

    \layout {
      \once \override Staff.Clef.stencil = ##f
      \once \override Staff.TimeSignature.stencil = ##f
      \once \override Staff.KeySignature.stencil = ##f
      ragged-right = ##f
    }
  }
}

\header {
  title = \realBookTitle
  tagline = ##f
}

theNotes = \relative c' {
  \set Staff.midiInstrument = "flute"
  \key f \major
  % \showStartRepeatBar
  \partial 8
  c8
  \bar "[|:"
  \repeat volta 2 {
    a'4 r g r
    \time 3/4
    f4 bes2
    \time 4/4
    \tuplet 3/2 { a4 g f } g4 a8 a~
    a2~ 8 es4 d8
    bes'4 r \tuplet 3/2 { d( c) bes }
    a8 g~ g2 f4
    a1
    \time 3/4
    b2 e,4
    \time 4/4
    \bar "||"
    \key a \major
    cis'2 e
    b4. e8~ e4 e,
    a2 cis
    gis4. cis8~ 2
    fis,2 gis4 a8 b~
    b a4. gis4 a
    e1~
    \time 3/4
    2 4
    \time 4/4
    cis'2 e4. fis8~
    4 e2 e,4
    fis2 a4. b8~
    4 a2.
    \bar "||"
    \key f \major
    d,2 e4( f)
    g4 f es des
    a'2.( c4~
    \time 3/4
    c4.) d,4 c8
    \bar ":|]"
  }
}
theChords = \chordmode {
  s8
  f2 a:7 |
  bes4:maj7 g2:m7.5- |
  bes2:maj7/c c:9 |
  es:11+ d:7.9- |
  g1:m7 |
  bes:m6 |
  b:m7 |
  e2.:9 |
  a1 |
  e/gis |
  fis:m |
  cis2:m/e a:9 |
  d2:maj7.9 d:6 |
  dis1:dim7 |
  e:sus4.7 |
  e2.:7 |
  a1 |
  cis:m7.5- |
  d |
  d:m6/f |
  bes:maj7 |
  g:m7.5- |
  f/c |
  bes2/c c4:7 |
}

theWords = \lyricmode {
  The quick brown fox jumps
  o -- ver the la -- zy dog __
  while the five box -- ing wi -- zards
  jump quick -- ly,
  oh Sphinx of black quartz,
  oh Sphinx of black quartz,
  dear Sphinx of black __ quartz judge my vow, __
  oh Sphinx of black quartz,
  my Sphinx of black quartz,
  Sphinx of __ black quartz judge my vow. __
  'cause the
}

\score {
  <<
    \new ChordNames \theChords
    \new Voice = vocalVoice \theNotes
    \new Lyrics \lyricsto vocalVoice \theWords
  >>

  \layout {
    % make only the first clef visible
    \override Score.Clef.break-visibility = #'#(#f #f #f)

    % make only the first time signature visible
    \override Score.KeySignature.break-visibility = #'#(#f #f #f)

    % allow single-staff system bars
    \override Score.SystemStartBar.collapse-height = #1
  }
}