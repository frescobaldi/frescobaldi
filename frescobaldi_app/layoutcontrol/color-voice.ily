% This file is part of the Frescobaldi project, http://www.frescobaldi.org/
%
% Copyright (c) 2011 - 2012 by Wilbert Berendsen
%
% This program is free software; you can redistribute it and/or
% modify it under the terms of the GNU General Public License
% as published by the Free Software Foundation; either version 2
% of the License, or (at your option) any later version.
%
% This program is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
% GNU General Public License for more details.
%
% You should have received a copy of the GNU General Public License
% along with this program; if not, write to the Free Software
% Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
% See http://www.gnu.org/licenses/ for more information.

\version "2.16.2"

\header {
  snippet-title = "Color a Voice"
  snippet-author = "Urs Liska"
  snippet-description = \markup {
    This colors a 'voice' with a given color.
    Depending on the used LilyPond version it uses or doesn't use
    the 'temporary' directive, which will make it behave nicer
    when reverting.
  }
  % add comma-separated tags to make searching more effective:
  tags = "color, preview, frescobaldi"
  % is this snippet ready?  See meta/status-values.md
  status = "ready" % aiming to be 'official'
}

% Function to determine the used LilyPond version.
\include "lilypond-version-predicates.ily"

colorVoiceTemporary = 
#(define-music-function (parser location color)
   (color?)
   ;; With newer LilyPond versions this improves the behaviour
   ;; of color-voices and color-directions.
   ;; When one of them is set and the other is set in addition,
   ;; now when the second is reverted the coloring of the first
   ;; will still be active.
   #{
     \temporary\override NoteHead #'color = #color
     \temporary\override Stem #'color = #color
     \temporary\override Beam #'color = #color
     \temporary\override Flag #'color = #color
     \temporary\override Accidental #'color = #color
   #})

colorVoiceOld = 
#(define-music-function (parser location color)
   (color?)
   #{
     \override NoteHead #'color = #color
     \override Stem #'color = #color
     \override Beam #'color = #color
     \override Flag #'color = #color
     \override Accidental #'color = #color
   #})

colorVoice = 
#(define-music-function (parser location color)
   (color?)
   (if (lilypond-greater-than-or-equal? '(2 17 6))
       ;; \temporary was introduced in 2.17.6
        #{ \colorVoiceTemporary #color #}
        #{ \colorVoiceOld #color #}
   ))

unColorVoice = 
#(define-music-function (parser location)()
   #{
     \revert NoteHead #'color
     \revert Stem #'color
     \revert Beam #'color
     \revert Flag #'color
     \revert Accidental #'color
   #})
     