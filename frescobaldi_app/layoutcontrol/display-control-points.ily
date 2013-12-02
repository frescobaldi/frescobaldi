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
  snippet-title = "Displaying control points of slurs and ties"
  snippet-author = "David Nalesnik, Thomas Morley, Urs Liska, Janek Warchoł"
  snippet-description = \markup {
    Slurs, Ties and other similar objects are drawn in LilyPond as
    third-order Bezier curves, which means that their shape is controlled
    by four "control-points" (first and last ones tell where the curve ends
    are placed, and the middle ones affect the curvature).  Changing the
    shape of these objects involves moving these control-points around,
    and it's helpful to see where they actually are.  This snippet defines
    a "\displayControlPoints" function that displays them.  You can use it
    by calling it inside your music expression, or by placing it in
    "\layout" block.  When used inside music expressions, it can be prefixed
    with "\once" in order to display only the control points of the curve that
    starts at this moment.
  }
  % add comma-separated tags to make searching more effective:
  tags = "slur, tie, bezier curve, control point, preview mode"
  % is this snippet ready?  See meta/status-values.md
  status = "ready" % aiming for status "official"
  %{
    NOTE:
    - Workaround for Tie formatting in 2.17 applied:
      \override Tie #'vertical-skylines = #'()
      through the use of 'lilypond-greater-than?' from
      lilypond-version-switch.ly, which has to be present too.
    - Code for printing of 1st/4th CP and line 2nd-3rd CP is
      present but commented out.
  %}
}

%%%%%%%%%%%%%%%%%%%%%%%%%%
% here goes the snippet: %
%%%%%%%%%%%%%%%%%%%%%%%%%%

% Define appearance
#(cond ((not (defined? 'debug-control-points-line-thickness))
        (define debug-control-points-line-thickness 0.05)))
#(cond ((not (defined? 'debug-control-points-cross-thickness))
        (define debug-control-points-cross-thickness 0.1)))
#(cond ((not (defined? 'debug-control-points-cross-size))
        (define debug-control-points-cross-size 0.7)))
#(cond ((not (defined? 'debug-control-points-color))
        (define debug-control-points-color red)))

\include "lilypond-version-predicates.ily"

#(define (make-cross-stencil coords cross-thickness arm-offset)
   ;; coords are the coordinates of the center of the cross
   (ly:stencil-add
    (make-line-stencil
     debug-control-points-cross-thickness
     (- (car coords) arm-offset)
     (- (cdr coords) arm-offset)
     (+ (car coords) arm-offset)
     (+ (cdr coords) arm-offset))
    (make-line-stencil
     debug-control-points-cross-thickness
     (- (car coords) arm-offset)
     (+ (cdr coords) arm-offset)
     (+ (car coords) arm-offset)
     (- (cdr coords) arm-offset))))

#(define (display-control-points)
   (lambda (grob)
     (let* ((grob-name (lambda (x) (assq-ref (ly:grob-property x 'meta) 'name)))
            (name (grob-name grob))
            (stil (cond ((or (eq? name 'Slur)
                             (eq? name 'PhrasingSlur))
                         (ly:slur::print grob))
                        ((eq? name 'LaissezVibrerTie)
                         (laissez-vibrer::print grob))
                        ((or (eq? name 'Tie)
                             (eq? name 'RepeatTie))
                         (ly:tie::print grob))))
            (ctrpts (ly:grob-property grob 'control-points))
            (cross-stencils
              (ly:stencil-add
                ;; to go from desired cross size (length of line)
                ;; to arm-offset, we have to divide by 2*sqrt(2)
                ;;
                ;; If you want to see the first and the last control-point, too,
                ;; uncomment the relevant lines.
                ;(make-cross-stencil (first ctrpts)
                  ;debug-control-points-cross-thickness
                  ;(/ debug-control-points-cross-size 2.8284))
                (make-cross-stencil (second ctrpts)
                  debug-control-points-cross-thickness
                  (/ debug-control-points-cross-size 2.8284))
                (make-cross-stencil (third ctrpts)
                  debug-control-points-cross-thickness
                  (/ debug-control-points-cross-size 2.8284))
                ;(make-cross-stencil (fourth ctrpts)
                  ;debug-control-points-cross-thickness
                  ;(/ debug-control-points-cross-size 2.8284))
                ))
            (line-stencils
               (ly:stencil-add
                (make-line-stencil debug-control-points-line-thickness
                  (car (first ctrpts)) (cdr (first ctrpts))
                  (car (second ctrpts))  (cdr (second ctrpts)))
                ;; If you want a line from second to third control-point uncomment
                ;; the following expression.
                ;(make-line-stencil debug-control-points-line-thickness
                ;  (car (second ctrpts)) (cdr (second ctrpts))
                ;  (car (third ctrpts))  (cdr (third ctrpts)))
                (make-line-stencil debug-control-points-line-thickness
                  (car (third ctrpts)) (cdr (third ctrpts))
                  (car (fourth ctrpts))  (cdr (fourth ctrpts)))
                ))
            )

       ;; The order of adding the stencils will determine which stencil is printed
       ;; below or above, similar to 'layer
       ;; TODO: Is there consensus about it?
       ;;
       ;; Setting the added stencils to empty extents solves the tie-issue for 2.16.2
       ;; but not for 2.17.x
       ;; I think there's still something fishy with the skyline-code.
       ;; Workaround: add \override Tie #'vertical-skylines = #'()
       ;; as shown in main function below.
       (ly:stencil-add stil
        ;; add crosses:
        (ly:make-stencil
         (ly:stencil-expr (stencil-with-color 
                           cross-stencils 
                           debug-control-points-color))
         empty-interval
         empty-interval)

         ;; add lines:
        (ly:make-stencil
         (ly:stencil-expr (stencil-with-color 
                           line-stencils 
                           debug-control-points-color))
         empty-interval
         empty-interval)
         empty-stencil))))

% turn on displaying control-points:
displayControlPoints = {
  % Workaround for Tie issue in 2.17:
  #(if (lilypond-greater-than? '(2 16 2))
       #{ \override Tie #'vertical-skylines = #'() #})
  \override Slur #'stencil = #(display-control-points)
  \override PhrasingSlur #'stencil = #(display-control-points)
  \override Tie #'stencil = #(display-control-points)
  \override LaissezVibrerTie #'stencil = #(display-control-points)
  \override RepeatTie #'stencil = #(display-control-points)
}

%%%%%%%%%%%%%%%%%%
% Enable display %
%%%%%%%%%%%%%%%%%%

\layout {
  \displayControlPoints
}
