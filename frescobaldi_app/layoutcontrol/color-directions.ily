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

\version "2.16.1"

\header {
  snippet-title = "Switch Based on LilyPond Version"
  snippet-author = "David Kastrup, Urs Liska, Janek Warchoł"
  snippet-description = \markup {
    Color objects whose directions have been set with
    the predefined shorthands or with direction operators.

    By default all grobs with a 'direction property are colored.
    This can be changed by defining debug-direction-grob-list
    with a list of grob names.
  }
  % add comma-separated tags to make searching more effective:
  tags = "Program flow, LilyPond versions"
  % is this snippet ready?  See meta/status-values.md
  status = "ready"
  first-known-supported-version = "2.16.1" % 2.16.0 doesn't work
  %{  
    TODO:
    - Are there more predefined shorthands to be redefined?
  %}
}

% Define appearance
#(cond ((not (defined? 'debug-direction-up-color))
        (define debug-direction-up-color blue)))
#(cond ((not (defined? 'debug-direction-down-color))
        (define debug-direction-down-color blue)))
#(cond ((not (defined? 'debug-direction-grob-list))
        (define debug-direction-grob-list 
          (map car all-grob-descriptions))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Directions set with ^ and _ %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

colorizeDirection =
#(define-music-function (parser location item)
  (symbol?)
  ;; see if the given grob has a (explicitly set) 'direction
  ;; and color it depending on the actual direction
  (define (grob-colorize-dir grob)
    (let ((ev (event-cause grob)))
      (case (and ev (ly:event-property ev 'direction))
              ((1) debug-direction-up-color)
              ((-1) debug-direction-down-color)
              (else '()))))
  #{ \override $(symbol->string item) #'color = #grob-colorize-dir #})

mapGrobList =
#(define-music-function (parser location)()
  ;; iterate over the given list of grob names and activate coloring
  #{ $@(map (lambda (s) #{ $colorizeDirection $s #}) debug-direction-grob-list) #})

% Activate the debug mode
\layout {
  \context {
    \Voice \mapGrobList
  }
}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Directions set with \xxxUp etc. %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

dynamicUp = {
  \dynamicUp
  \override DynamicText #'color = #debug-direction-up-color
  \override DynamicLineSpanner #'color = #debug-direction-up-color
  \override DynamicTextSpanner #'color = #debug-direction-up-color
  \override Hairpin #'color = #debug-direction-up-color
}

dynamicDown = {
  \dynamicDown
  \override DynamicText #'color = #debug-direction-down-color
  \override DynamicLineSpanner #'color = #debug-direction-down-color
  \override DynamicTextSpanner #'color = #debug-direction-down-color
  \override Hairpin #'color = #debug-direction-down-color
}

dynamicNeutral = {
  \dynamicNeutral
  \revert DynamicText #'color
  \revert DynamicLineSpanner #'color
  \revert DynamicTextSpanner #'color
  \revert Hairpin #'color
}


slurUp = {
  \slurUp
  \override Slur #'color = #debug-direction-up-color
}

slurDown = {
  \slurDown
  \override Slur #'color = #debug-direction-down-color
}

slurNeutral = {
  \slurNeutral
  \revert Slur #'color
}

phrasingSlurUp = {
  \phrasingSlurUp
  \override PhrasingSlur #'color = #debug-direction-up-color
}

phrasingSlurDown = {
  \phrasingSlurDown
  \override PhrasingSlur #'color = #debug-direction-down-color
}

phrasingSlurNeutral = {
  \phrasingSlurNeutral
  \revert PhrasingSlur #'color
}

tieUp = {
  \tieUp
  \override Tie #'color = #debug-direction-up-color
}

tieDown = {
  \tieDown
  \override Tie #'color = #debug-direction-down-color
}

tieNeutral = {
  \tieNeutral
  \revert Tie #'color
}

\include "color-voice.ily"

stemUp = {
  \stemUp
  \colorVoice #debug-direction-up-color
}

stemDown = {
  \stemDown
  \colorVoice #debug-direction-down-color
}

stemNeutral = {
  \stemNeutral
  \unColorVoice
}
