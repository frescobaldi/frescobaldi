\version "2.19.82"
% To be compiled with -dcrop to .svg and cropped again in (e.g.) Inkscape
{
  \omit Staff.StaffSymbol
  \omit Staff.Clef
  \omit Staff.TimeSignature
  \omit Staff.NoteHead
  \omit Staff.Stem
  <<
    {
      \voiceOne
      g'' \fermata
    }
    \new Voice {
      \voiceTwo
      \once \override Script.extra-offset = #'(0 . 3)
      g''\fermata
    }
  >>
}