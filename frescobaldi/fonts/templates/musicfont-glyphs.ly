% Basic font test, glyph sampler
% Provided by Abraham Lee

\include "english.ly"
\header {
  title = "BASIC FONT TEST"
  tagline = ##f
}

highlight = {
  \once \override Script.color = #red
  \once \override Voice.TrillSpanner.color = #red
  \once \override Fingering.color = #red
  \once \override BreathingSign.color = #red
  \once \override StaffGroup.SystemStartBracket.color = #red
  \once \override StaffGroup.SystemStartBrace.color = #red
  \once \override Score.SustainPedal.color = #red
}

#(define ((fakeTimeSig time-sig) grob)
   (grob-interpret-markup grob
     (markup #:compound-meter time-sig)))

%%%% TIME SIGNATURES
\score {
  \layout {
    indent = 0\in
    ragged-right = ##f
    ragged-last = ##f
  }
  \header {
    piece = "Time Signatures"
  }
  {
    \new Staff \with {
      \omit Clef
      \remove Bar_engraver
      \override TimeSignature.break-visibility = #all-visible
    }{
      \time 4/4
      s1
      \time 2/2
      s
      \override Staff.TimeSignature.stencil = #(fakeTimeSig '(1 2))
      \time 4/4
      s
      \override Staff.TimeSignature.stencil = #(fakeTimeSig '(3 4))
      \time 4/4
      s
      \override Staff.TimeSignature.stencil = #(fakeTimeSig '(15 16))
      \time 4/4
      s
      \override Staff.TimeSignature.stencil = #(fakeTimeSig '(7 8))
      \time 4/4
      s
      \override Staff.TimeSignature.stencil = #(fakeTimeSig '((10 8) (9 8)))
      \time 4/4
      s
    }
  }
}

%%%% CLEFS
\score {
  \layout {
    indent = 0\in
    ragged-right = ##f
    ragged-last = ##f
  }
  \header {
    piece = "Clefs"
  }
  {
    \new Staff \with {
      \remove Bar_engraver
      \remove Time_signature_engraver
    }{
      \override Staff.Clef.full-size-change = ##t
      \clef treble
      s8
      \clef alto
      s8
      \clef bass
      s8
      %\once \useEmm Staff.Clef
      \clef tab
      s8
      \clef percussion
      s8
      \revert Staff.Clef.full-size-change
      \clef treble
      s8
      \clef alto
      s8
      \clef bass
      s8
      %\once \useEmm Staff.Clef
      \clef tab
      s8
      \clef percussion
      s8
    }
  }
}

%%%% NOTEHEADS
\score {
  \header {
    piece = "Noteheads"
  }
  \layout {
    indent = 0\in
    ragged-right = ##f
    ragged-last = ##f
    \context {
      \Score
      \remove Bar_number_engraver
    }
  }
  {
    \new Staff \with {
      \omit Clef
      \remove Bar_engraver
      \remove Time_signature_engraver
      %\override NoteHead.style = #'altdefault
    } {
      % BREVE NOTEHEADS
      \time 3/1
      \newSpacingSection
      \override Score.SpacingSpanner.spacing-increment = #1.5
      <<
        \relative c''' {
          a\breve
          <d, a' c e>\breve
          b'\breve
          <c, b' d f>\breve
          <a' b c>\breve
        } \\
        \relative c' {
          a\breve
          <a c e b'>\breve
          b\breve
          <e, g b a'>\breve
          <a b c>\breve
        }
      >>
      \relative c' {
        <g' a b c>\breve
      }
      % WHOLE NOTEHEADS
      \time 2/4
      <<
        \relative c''' {
          a1
          <d, a' c e>1
          b'1
          <c, b' d f>1
          <a' b c>1
        } \\
        \relative c' {
          a1
          <a c e b'>1
          b1
          <e, g b a'>1
          <a b c>1
        }
      >>
      \relative c' {
        <g' a b c>1
      }
      \break
      % HALF NOTEHEADS
      \newSpacingSection
      \override Score.SpacingSpanner.spacing-increment = #2.3
      <<
        \relative c''' {
          \clef treble
          a2
          <d, a' c e>2
          b'2
          <c, b' d f>2
          <a' b c>2
        } \\
        \relative c' {
          a2
          <a c e b'>2
          b2
          <e, g b a'>2
          <a b c>2
        }
      >>
      \relative c' {
        <g' a b c>2
      }
      % QUARTER NOTEHEADS
      \time 2/2
      <<
        \relative c''' {
          a4
          <d, a' c e>4
          b'4
          <c, b' d f>4
          <a' b c>4
        } \\
        \relative c' {
          a4
          <a c e b'>4
          b4
          <e, g b a'>4
          <a b c>4
        }
      >>
      \relative c' {
        <g' a b c>4
      }
    }
  }
}

%%%% RESTS
\score {
  \header {
    piece = "Rests"
  }
  \layout {
    indent = 0\in
    ragged-right = ##f
    ragged-last = ##f
  }
  {
    \new Staff \with {
      \omit Clef
      \remove Bar_engraver
      \remove Time_signature_engraver
    } {
      \time 16/1
      r\maxima
      \newSpacingSection
      r\longa
      \newSpacingSection
      r\breve
      \newSpacingSection
      r1 r2 r4 r8 r16 r32 r64 r128
    }
  }
}

%%%% FLAGS
\score {
  \header {
    piece = "Flags"
  }
  \layout {
    indent = 0\in
    ragged-right = ##f
    ragged-last = ##f
  }
  {
    \new Staff \with {
      \omit Clef
      \remove Bar_engraver
      \remove Time_signature_engraver
    } {
      \newSpacingSection
      \override Score.SpacingSpanner.spacing-increment = #2
      <<
        \relative c' {
          s128 f128
          s64 f64
          s32 f32
          s16 f16
          s8 \slashedGrace f8 f8.
        }
        \\
        \relative c'' {
          e128 s128
          \newSpacingSection
          e64 s64
          \newSpacingSection
          e32 s32
          \newSpacingSection
          e16 s16
          \newSpacingSection
          \slashedGrace e8 e8. s8
        }
      >>
    }
  }
}

%%%% DYNAMICS
\score {
  \header {
    piece = "Dynamics"
  }
  \layout {
    indent = 0\in
    ragged-right = ##f
    ragged-last = ##f
  }
  \new Staff \with {
    \omit Clef
    \remove Bar_engraver
    \remove Time_signature_engraver
  } \relative c'' {
    \autoBeamOff
    \override Score.SpacingSpanner.spacing-increment = #2.75
    \override DynamicLineSpanner.staff-padding = #2.0
    e8\ffff
    e\fff
    e\ff
    e\f
    e\mf
    e\mp
    e\p
    e\pp
    e\ppp
    e\pppp
    e\fp
    e\fz
    e\sf
    e\sfz
    e\rfz
  }
}

\pageBreak

%%%% ARTICULATIONS
\score {
  \layout {
    indent = 0\in
    ragged-right = ##f
    ragged-last = ##f
  }
  \header {
    piece = "Articulations"
  }
  {
    \new Staff \with {
      \omit Clef
      \remove Time_signature_engraver
    } { \cadenzaOn \relative c'' {
      \autoBeamOff
      \override Score.SpacingSpanner.spacing-increment = #3.0
      e8\staccato
      e\staccatissimo
      e\accent%^\arnoldVaraccent
      e\marcato
      e\tenuto
      e\portato
      e \startTrillSpan
      \parenthesize e \stopTrillSpan
      %\useEmm Script
      e\prall
      e\downprall
      e\pralldown
      e\upprall
      e\prallup
      e\prallprall
      e\lineprall
      \breathe
      \bar "" \break
      e8\downbow
      e\upbow
      e\flageolet
      e\open
      e\halfopen
      e\stopped
      e\thumb
      e\snappizzicato
      %\undo \useEmm Script
      e\espressivo
      %\useEmm Script
      e\mordent
      e\prallmordent
      e\downmordent
      e\upmordent
      e\turn
      e\reverseturn
      \override BreathingSign.text = \markup { \musicglyph #"scripts.rvarcomma" }
      \breathe
      \bar "" \break
      e8^\lheel
      e\rheel
      e^\ltoe
      e\rtoe
      e\shortfermata
      %\undo \useEmm Script
      e\fermata
      %\useEmm Script
      e\longfermata
      e\verylongfermata
      %\undo \useEmm Script
      e\segno
      e\coda
      e\varcoda
      e:16
      e:32
      <e, a c e a>\arpeggio
      \arpeggioArrowUp <a c e a c>\arpeggio
        }
        \bar "" \break
        \relative c' {
          e8\staccato%^\hauptstimme
          e\staccatissimo%^\arnoldWeakbeat
          e\accent%^\endstimme
          e\marcato%^\nebenstimme
          e\tenuto%^\arnoldStrongbeat
          e\portato%^\endstimme
          \override TrillSpanner.direction = #DOWN
          e\startTrillSpan
          e\stopTrillSpan
          %\useEmm Script
          e_\prall
          e_\downprall
          e_\pralldown
          e_\upprall
          e_\prallup
          e_\prallprall
          e_\lineprall
          %\once \useEmm BreathingSign
          \override BreathingSign.text = \markup { \musicglyph #"scripts.caesura.curved" }
          \breathe
          \bar "" \break
          e8_\downbow
          e_\upbow
          e_\flageolet
          e_\open
          e_\halfopen
          e_\stopped
          e_\thumb
          e_\snappizzicato
          %\undo \useEmm Script
          e\espressivo
          %\useEmm Script
          e_\mordent
          e_\prallmordent
          e_\downmordent
          e_\upmordent
          e_\turn
          e_\reverseturn
          %\once \useEmm BreathingSign
          \override BreathingSign.text = \markup { \musicglyph #"scripts.caesura.straight" }
          \breathe
          \bar "" \break
          e8_\lheel
          e_\rheel
          e_\ltoe
          e_\rtoe
          e_\shortfermata
          %\undo \useEmm Script
          e_\fermata
          %\useEmm Script
          e_\longfermata
          e_\verylongfermata
          %\undo \useEmm Script
          e_\segno
          e_\coda
          e_\varcoda
          e:16 \sustainOn
          e:32 \sustainOff
          e:64
          \arpeggioArrowDown <g, c e g c>\arpeggio
          \override BreathingSign.text = \markup { \musicglyph #"scripts.tickmark" }
          \breathe
    } }
  }
}

% KEY SIGNATURES
\score {
  \layout {
    indent = 0\in
    ragged-right = ##f
    ragged-last = ##f
  }
  \header {
    piece = "Key Signatures"
  }
  {
    \new Staff \with {
      \remove Time_signature_engraver
      \remove Bar_engraver
      %\omit Clef
    }{
      \clef treble
      \time 4/4
      \key cs \major
      s8
      \key c \major
      s8
      \key cf \major
      s8
      \override Staff.Clef.full-size-change = ##t
      \clef bass
      \key cf \major
      s8
      \key c \major
      s8
      \key cs \major
      s8
    }
  }
}

% ACCIDENTALS
\score {
  \layout {
    indent = 0\in
    ragged-right = ##f
    ragged-last = ##f
    \context {
      \Score
      \remove Bar_number_engraver
    }
    \context {
      \Staff
      \omit Clef
      \remove Time_signature_engraver
      \remove Bar_engraver
    }
  }
  \header {
    piece = "Braces, Brackets, & Accidentals"
  }
  <<
    \new StaffGroup <<
      \new GrandStaff <<
        \new Staff \relative c'{
          \time 3/1
          <fff! gff! aff! bff! cff! dff! eff!>1
          s2
          <fff? gff? aff? bff? cff? dff? eff?>1
          s2
        }
        \new Staff \relative c'{
          \time 3/1
          \clef treble
          <ff! gf! af! bf! cf! df! ef!>1
          s2
          <ff? gf? af? bf? cf? df? ef?>1
          s2
        }
      >>
    >>
    \new StaffGroup <<
      \new GrandStaff <<
        \new Staff \relative c'{
          \time 3/1
          \clef treble
          <f! g! a! b! c! d! e!>1
          s2
          <f? g? a? b? c? d? e?>1
          s2
        }
        \new Staff \relative c'{
          \time 3/1
          \clef treble
          <fs! gs! as! bs! cs! ds! es!>1
          s2
          <fs? gs? as? bs? cs? ds? es?>1
          s2
        }
        \new Staff \relative c'{
          \time 3/1
          \clef treble
          <fss! gss! ass! bss! css! dss! ess!>1
          s2
          <fss? gss? ass? bss? css? dss? ess?>1
          s2
        }
      >>
    >>
  >>
}