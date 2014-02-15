\version "2.18.0"

\paper {
  oddFooterMarkup = ##f
  evenFooterMarkup = ##f
  oddHeaderMarkup = ##f
  evenHeaderMarkup = ##f
  
  top-margin = 0
  bottom-margin = 0
  left-margin = 0
  right-margin = 0

  top-markup-spacing = #
  '((minimum-distance . 0)
    (basic-distance . 0)
    (padding . 0)
    (stretchability . 0))

  last-bottom-spacing = #
  '((minimum-distance . 0)
    (basic-distance . 0)
    (padding . 0)
    (stretchability . 0))

}

\layout {
  indent = #0
}

%%% Thanks to: http://lists.gnu.org/archive/html/lilypond-user/2011-03/msg00270.html
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

alignGrob =
#(define-music-function (parser location grob-to-align reference-grob dir corr) (list? symbol? integer? number?)
  #{
     \overrideProperty #(append grob-to-align (list 'after-line-breaking))
     #(lambda (grob)
        (let* ((sys (ly:grob-system grob))
               (array (ly:grob-object sys 'all-elements))
               (len (ly:grob-array-length array))
               (current-grob-in-search (lambda (q)
                                         (assq-ref (ly:grob-property (ly:grob-array-ref array q) 'meta) 'name)))
               (default-coord (ly:grob-relative-coordinate grob sys X))
               (lst '()))
          
          ;; find all instances in a system of the grob we want to use for alignment
          (let lp ((x 0))
            (if (< x len)
                (begin
                 (if (eq? reference-grob (current-grob-in-search x))
                     (set! lst
                           (cons (ly:grob-array-ref array x) lst)))
                 (lp (1+ x)))))
          
          ;; find the grob with the X-coordinate closest to object to be aligned
          (let ((ref (car lst)))
            (define closest (lambda (x)
                              (if (< (abs (- default-coord
                                            (ly:grob-relative-coordinate (car x) sys X)))
                                     (abs (- default-coord
                                            (ly:grob-relative-coordinate ref sys X))))
                                  (set! ref (car x)))
                              (if (not (null? (cdr x)))
                                  (closest (cdr x)))))
            
            (closest lst)
            ;; calculate offset to X based on choice of alignment
            (ly:grob-set-property! grob 'extra-offset
              `(,(cond ((eq? dir -1) (- (ly:grob-relative-coordinate ref sys X)
                                        default-coord))
                   ((eq? dir 0)  (- (interval-center (ly:grob-extent ref sys X))
                                    (interval-center (ly:grob-extent grob sys X))))
                   ((eq? dir 1)  (- (cdr (ly:grob-extent ref sys X))
                                    (cdr (ly:grob-extent grob sys X)))))
                 
                 . ,corr)))))
   #}
   )

