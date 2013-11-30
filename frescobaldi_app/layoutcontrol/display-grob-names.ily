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
  snippet-title = "Displaying Grob Names of objects"
  snippet-author = "Thomas Morley, Urs Liska"
  % taken from this thread on the mailing list:
  % http://lists.gnu.org/archive/html/lilypond-user/2013-03/msg01048.html
  snippet-description = \markup {
    This snippet prints the names of all objects.
    While this doesn't help in debugging a layout directly
    it can be useful (for beginners) to find the right
    information in the documentation.
  }
  % add comma-separated tags to make searching more effective:
  tags = "preview mode, debug layout, grob name"
  % is this snippet ready?  See meta/status-values.md
  status = "unfinished"
  %{
    TODO:
    - Enable to do it \once
    because this is very intrusive otherwise
  %}
}

% Define appearance
#(cond ((not (defined? 'debug-grob-names-color))
        (define debug-grob-names-color darkcyan)))
% Which grobs to print the dot to?
% Possible values:
% - 'all-grobs
% - Name of a grob (as symbol)
% - List of grob names
#(cond ((not (defined? 'debug-grob-names-grob-list))
        ;(define debug-grob-names-grob-list '(NoteHead Stem))))
        ;(define debug-grob-names-grob-list 'NoteHead )))
        (define debug-grob-names-grob-list 
          (map car all-grob-descriptions))))

#(define (add-text)
   (lambda (grob)
     (let* ((layout (ly:grob-layout grob))
            (props (layout-extract-page-properties layout))
            (font
             (ly:paper-get-font layout
               (cons '((font-encoding . fetaMusic)) props)))
            ;; Get the stencil-procedure from ly:grob-basic-properties.
            ;; If any, use it to create the stencil.
            (function (assoc-get 'stencil (ly:grob-basic-properties grob)))
            (stencil (if function (function grob) point-stencil))
            ;; Get the grob-name and create a text-stencil.
            ;; Read out the y-length for later translate.
            (grob-name-proc
             (lambda (x) (assq-ref (ly:grob-property x 'meta) 'name)))
            (grob-name (grob-name-proc grob))
            (grob-string (if (symbol? grob-name)
                             (symbol->string grob-name)
                             "no name"))
            (ref-text-stil (grob-interpret-markup grob
                             (markup
                              #:with-color debug-grob-names-color
                              #:normal-text
                              #:abs-fontsize 6
                              (string-append "   " grob-string))))
            (ref-text-stil-length
             (interval-length (ly:stencil-extent ref-text-stil Y)))
            (grob-string-stil (grob-interpret-markup grob
                                          (markup
                                           #:with-dimensions '(0 . 0) '(0 . 0)
                                           #:stencil
                                           ref-text-stil))))

       ;; If there's a grob with stencil-procedure and a valid stencil is
       ;; created, add the red-dot-stil and an optional text-stencil.
       (if (and function (ly:stencil? stencil) (grob::is-live? grob))
           (ly:grob-set-property! grob 'stencil
             (ly:stencil-add
              stencil
              (ly:stencil-translate-axis
                   (ly:stencil-rotate
                    grob-string-stil
                    45 0 0)
                   (/ ref-text-stil-length 2)
                   X)))))))

% needs to be here for 2.16.2
#(define-public (symbol-list-or-symbol? x)
   (if (list? x)
       (every symbol? x)
       (symbol? x)))

#(define (add-grob-names l)
   ;; possible values for l:
   ;;   'all-grobs (adds text to all grobs, where possible)
   ;;          this will naturally cause collisions,
   ;;   a single grob-name, must be a symbol,
   ;;   a list of grob-names,
   ;;   anything else (returns the unchanged original stencil)
   ;;  TODO: How to apply it once?
   (let ((grobs-to-consider
            (cond
             ((symbol? l)
             (list (assoc l all-grob-descriptions)))
            ((list? l)
             (map
              (lambda (grob)
                (assoc grob all-grob-descriptions))
              l))
            (else '()))))
     (lambda (context)
       (let loop ((x grobs-to-consider))
         (if (not (null? x))
             (let ((grob-name (caar x)))
               (ly:context-pushpop-property
                context
                grob-name
                'after-line-breaking
                (add-text))
               (loop (cdr x))))))))

printGrobNames =
#(define-music-function (parser location s-or-l)(symbol-list-or-symbol?)
   "
       Will add a red text to each (specified) grob's ref-point .
 Valid input for s-or-l:
      @code{'all-grobs}, (adds red-dots to all grobs, where possible), this will
          naturally cause collisions
      a single grob-name, must be a symbol,
      a list of grob-names.
 To avoid bleeding-overs any context has to be initiated explicitly.
"
#{
  \applyContext #(add-grob-names s-or-l)
#})


\layout {
  \context {
    \Voice
    \printGrobNames #debug-grob-names-grob-list
  }
}
