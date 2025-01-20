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


\include "./lilypond-version-predicates.ily"

#(define-macro (define-default sym val)
  `(define ,sym
     (if (defined? ',sym)
         ,sym
         ,val)))

#(define (string-or-false? x)
   (or (string? x)
       (not x)))

debugLayoutOption =
#(define-void-function (parser location option-name filename)
   (symbol? string-or-false?)
    (if (ly:get-option option-name)
        ;; conditionally choose the syntax to include a file
        ;; based on the current LilyPond version
        (if (lilypond-greater-than? '(2 19 21))
            (ly:parser-include-string (format #f "\\include \"./~a\"" filename))
            (ly:parser-include-string parser (format #f "\\include \"./~a\"" filename)))))

%% Add a custom file for debugging layout. Include it first:
%% this way it can for example define configuration variables.
\debugLayoutOption #'debug-custom-file
                   #(let ((custom-file (ly:get-option 'debug-custom-file)))
                      (and custom-file (symbol->string custom-file)))

%% include preview options depending on the
%% presence or absence of command line switches

\debugLayoutOption #'debug-voices "color-voices.ily"

%% color grobs switched with \xxxUp or \xxxDown
\debugLayoutOption #'debug-directions "color-directions.ily"

%% Add a dot for the anchor of each grob
\debugLayoutOption #'debug-grob-anchors "display-grob-anchors.ily"

%% Add a dot for the anchor of each grob
\debugLayoutOption #'debug-grob-names "display-grob-names.ily"

\debugLayoutOption #'debug-paper-columns "info-paper-columns.ily"

%% display skylines
%% -> this is very intrusive, so handle with care!
%% should be switched off by default
#(if (ly:get-option 'debug-display-skylines)
     (ly:set-option 'debug-skylines #t))

%% the option should be named debug-skylines,
%% this name clash has to be resolved!

%% Add a dot for the anchor of each grob
\debugLayoutOption #'debug-annotate-spacing "annotate-spacing.ily"
