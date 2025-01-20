#(set-global-staff-size #20) \paper { ragged-right = ##f }

\version "2.19.21"

\header{
  composer = \markup \typewriter "J.S. Bach"
  title = "Wenn wir in höchsten Nöten sein (BWV 641)"
  subtitle = \markup \sans "Analysis from Gene Biringer's Schenker Text, Ex. 5-27"
  enteredby = "Kris Shaffer, Werner Lemberg"
}


setup = { \oneVoice
          \override NoteColumn.ignore-collision = ##t }


% Some remarks.
%
% - Number `i' in the comments below gives the `i'th column in the graph.
%   Rhythmically, every column is (arbitrarily) represented as an eighth.
%   In total, the graph has 15 columns.
%
% - Using `\stemUp' and `\stemDown' influences the positioning of slurs even
%   if `\omit Stem' disables printing of stems.
%
% - Since each layer of the Schenker graph uses `\\' to create a new voice
%   it is not necessary to undo `\omit' or `\hide' commands.  The same holds
%   for overridden properties.
%
%   The `price' for using `\\' is to call the above-defined macro `\setup'
%   at the beginning of each voice to undo horizontal voice shifts and to
%   make LilyPond ignore collisions.
%
% - Trailing (musical) skips in voices are omitted.


rightHand = {
  \clef treble
  \key g \major

  <<
    {
      \setup
      % This produces half notes as note heads of eighths.
      \override NoteHead.duration-log = #1

  % 1
      s2
  % 5
      b'8 -\tweak positions #'(8 . 8) ^[
        ^\markup { \override #'(baseline-skip . 0.8)
                   \column { \with-color #red \small { ^ 3 } } }
      s4.
  % 9
      s4 a'8
        ^\markup { \override #'(baseline-skip . 0.8)
                   \column { \with-color #red \small { ^ 2 } } }
      s8
  % 13
      s4 g'8]
        ^\markup { \override #'(baseline-skip . 0.8)
                   \column { \with-color #red \small { ^ 1 } } }
    }
  \\
    {
      \setup
      \override Slur.color = #(x11-color "purple")
      \stemUp
      \omit Stem
      \hide NoteHead
      \slurDashed

  % 1
      s2
  % 5
      b'2 -\tweak height-limit #6 _(
  % 9
      b'4)
      a'4 -\tweak height-limit #3.25 _(
  % 13
      s8
      a'4)
    }
  \\
    {
      \setup

  % 1
      \stemUp
      g'8 -\tweak positions #'(4.5 . -3.25) -[ s4.
  % 5
      \stemDown
      \once \hide NoteHead
      b'8]
      \stemUp
      a'8 -\tweak positions #'(3 . -3) -[ s
      \stemDown
      c''8]
    }
  \\
    {
      \setup
      \override Slur.color = #(x11-color "violet")

  % 1
      \stemDown
      \omit Stem
      \omit Flag
      s8 fis'^(_\markup { \with-color #blue \tiny N } g')
      a'8^(^\markup { \with-color #blue \tiny P }
  % 5
      \hideNotes
      b'4)
      \unHideNotes
      \once \override TextScript.outside-staff-priority = ##f
      b'8^(^\markup { \with-color #blue \tiny P }
      \undo \omit Stem
      \undo \omit Flag
      \stemUp
      \override Stem.length = #10
      c''8)^(
  % 9
      \override Stem.length = #14
      b'4) s8
      \stemDown
      \omit Stem
      \omit Flag
      c''8^(
  % 13
      b'8_\markup { \with-color #blue \tiny P } a')
    }
  \\
    {
      \setup
      \override Slur.color = #(x11-color "violet")

  % 1
      \stemUp
      \omit Stem
      \omit Flag
      g'8_( fis' g'4)
  % 5
      s2
  % 9
      s2
  % 13
      b'8_( a')
    }
  \\
    {
      \setup
      \omit Stem
      \hide NoteHead

  % 1
      s2
  % 5
      s8 d'4
      \change Staff = "LH"
      b4
    }
  \\
    {
      \setup
      \omit Stem
      \hide NoteHead

  % 1
      s2
  % 5
      s2
  % 9
      s4
      d'4
      \change Staff = "LH"
  % 13
      b4
    }
  >>

  \bar "|."
}


leftHand = {
  \clef bass
  \key g \major

  <<
    {
      \setup
      % This produces half notes as note heads of eighths.
      \override NoteHead.duration-log = #1

  % 1
      g8 -\tweak positions #'(-8 . -8) _[
        _\markup { \with-color #(x11-color 'LawnGreen) \bold I }
      s4.
  % 5
      s2
  % 9
      s2
  % 13
      d8_\markup { \with-color #(x11-color 'LawnGreen) \bold V }
      s8
      g,8]_\markup { \with-color #(x11-color 'LawnGreen) \bold I }
    }
  \\
    {
      \setup
      \override Slur.color = #(x11-color "violet")
      \stemUp
      \hide Stem
      \hide Flag

  % 1
      s8
      \once \override TextScript.outside-staff-priority = ##f
      \once \override TextScript.padding = #1
      a8_(^\markup { \with-color #blue \tiny P } b)
      \stemDown
      fis8^(^\markup { \with-color #blue \tiny P }
  % 5
      e8)
      c8 -\tweak height-limit #1.5 ^(
      d8)^\markup { \with-color #blue \tiny N }
      \stemUp
      fis,8_(
  % 9
      \undo \hide Stem
      \undo \hide Flag
      \override Stem.length = #10
      \stemDown
      g,4)
      c8_(
      \hide Stem
      \hide Flag
      a,8)
  % 13
      \once \hide NoteHead
      d8^( d,)
    }
  \\
    {
      \setup
      \override Slur.color = #(x11-color "violet")

  % 1
      \hide Stem
      \hide Flag
      \hide NoteHead
      g4 -\tweak height-limit #4 ^( b8) s8
  % 5
      s8
      \undo \hide Stem
      \undo \hide NoteHead
      \override Beam.positions = #'(-4 . 1)
      \stemDown
      c8[ s
      \stemUp
      fis,8]
  % 9
      \override Beam.positions = #'(1 . -4)
      g,8[
      \stemDown
      b,8]
      \hide Stem
      \hide NoteHead
      c8^( s
  % 13
      d4)
    }
  \\
    {
      \setup
      \override Slur.color = #(x11-color "violet")
      \hide Stem
      \hide NoteHead

  % 1
      g2 -\tweak height-limit #3 _(
  % 5
      e4)
    }
  \\
    {
      \setup
      \override Slur.color = #(x11-color "purple")
      \hide Stem
      \hide NoteHead
      \slurDashed

  % 1
      g2 -\tweak height-limit #8 _(
  % 5
      s2
  % 9
      g,4)
    }
  >>

  \bar "|."
}


\score {
  \new PianoStaff
  <<
    \new Staff = "RH" \rightHand
    \new Staff = "LH" \leftHand
  >>

  \layout {
    \context {
      \Score
      timing = ##f
      \override StaffGrouper.staff-staff-spacing.basic-distance = #13 }

    \context {
      \Staff
      \remove "Time_signature_engraver" }

    \context {
      \PianoStaff
      followVoice = ##t }

    \context {
      \Voice
      % We use `VoiceFollower' lines to indicate related columns
      % instead of related voices; we thus avoid vertical offsets.
      \override VoiceFollower.bound-details.left.padding = #0
      \override VoiceFollower.bound-details.right.padding = #0 }
  }
}
