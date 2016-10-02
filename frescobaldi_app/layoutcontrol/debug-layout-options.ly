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

%{
  This file is included (through -dinclude-settings)
  by Frescobaldi's Preview compilation mode.
  It checks for the presence of certain command line options
  (which are also inserted by the Preview mode)
  to switch some layout debugging features on or off.
  This design has been chosen to simplify a future
  integration of the functionality into LilyPond proper.
  Then the following code has to be run inside LilyPond
  when a -ddebug-layout command line option is present.
  
  For an inclusion in LilyPond the strategy has to be modified:
  Currently all options have to be explicitly activated.
  This is because we have the checkbox UI in Frescobaldi.
  When implemented as LilyPond command line option we will
  define a default set of options that is activated by
  -ddebug-layout, while some additional options can be
  activated and the default options be deactivated with
  command line options or #(ly:set-option ...) commands.
%}

debugLayoutOptions =
#(define-void-function (parser location)()
   (define (parser-include-string-comp parser str)
       (if (let ((v (ly:version)))
           (or (> (first  v)  2)
                (> (second v) 19)
                (>= (third v) 22)))
           (ly:parser-include-string str)
           (ly:parser-include-string parser str)))
   ;; include the optional custom file first.
   ;; This way it can for example define configuration variables.
   (if (ly:get-option 'debug-custom-file)
       ;; Add a custom file for debugging layout
       (parser-include-string-comp parser 
         (format "\\include \"~A\"\n" (ly:get-option 'debug-custom-file))))
   ;; include preview options depending on the
   ;; presence or absence of command line switches
   (if (ly:get-option 'debug-control-points)
       ;; display control points
       (parser-include-string-comp parser "\\include \"display-control-points.ily\""))
   (if (ly:get-option 'debug-voices)
       ;; color \voiceXXX music
       (parser-include-string-comp parser "\\include \"color-voices.ily\""))
   (if (ly:get-option 'debug-directions)
       ;; color grobs switched with \xxxUp or \xxxDown
       (parser-include-string-comp parser "\\include \"color-directions.ily\""))
   (if (ly:get-option 'debug-grob-anchors)
       ;; Add a dot for the anchor of each grob
       (parser-include-string-comp parser "\\include \"display-grob-anchors.ily\""))
   (if (ly:get-option 'debug-grob-names)
       ;; Add a dot for the anchor of each grob
       (parser-include-string-comp parser "\\include \"display-grob-names.ily\""))
   (if (ly:get-option 'debug-paper-columns)
       ;; Add a dot for the anchor of each grob
       (parser-include-string-comp parser "\\include \"info-paper-columns.ily\""))
   (if (ly:get-option 'debug-display-skylines)
       ;; display skylines
       ;; -> this is very intrusive, so handle with care!
       ;; should be switched off by default
       (ly:set-option 'debug-skylines #t))
       ;; the option should be named debug-skylines,
       ;; this name clash has to be resolved!
   (if (ly:get-option 'debug-annotate-spacing)
       ;; Add a dot for the anchor of each grob
       (parser-include-string-comp parser "\\include \"annotate-spacing.ily\"")))

\debugLayoutOptions

%{
  The following code should later be included in LilyPond's
  initialisation phase, at a point
  when any (ly:set-option ...) commands in the input file(s) have
  been already parsed.
  
#(if (ly:get-option 'debug-layout)
     ;; check for additional command line options
     #{
       \debugLayoutOptions
     #})

%}
