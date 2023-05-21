\version "2.18.2"
%{


xml-export.ily

Written by Wilbert Berendsen, jan-feb 2015


This LilyPond module defines a function (xml-export) that converts LilyPond
datastructures to XML. For convenience, a \displayLilyXML music function is
added that converts a music expression to XML.

Usage e.g.:

  \include "/path/to/xml-export.ily"
  \displayLilyXML { c d e f }

The XML closely follows the LilyPond music structure.

All (make-music 'MusicName ...) objects translate to a <music type="MusicName">
tag. The music in the 'element and 'elements properties is put in the <element>
and <elements> tags. (LilyPond uses 'element when there is a single music
argument, and 'elements for a list of music arguments, but for example \repeat
uses both: 'element for the repeated music and 'elements for the \alternatives.)

Thus <element>, if there, always has one <music> child. <elements>, if there,
can have more than one <music> child.

Besides 'element and 'elements, the following properties of music objects are
handled specially:

- 'origin => <origin> element with filename, line and char attributes
- 'pitch => <pitch> element with octave, notename and alteration attributes
- 'duration => <duration> element with log, dots, numer and denom attributes
- 'articulations => <articulations> element containing <music> elements
- 'tweaks => <tweaks> element containing pairs (symbol . value)

All other properties a music object may have, are translated to a <property>
element with a name attribute. The value is the child element and can be any
object (string, list, pair, symbol, number etc.). (Note that the LilyPond
command \displayMusic does not display all properties.)

Markup objects are also converted to XML, where a toplevel <markup> element
is used. The individual markup commands are converted to an <m> element, with
the name in the name attribute (e.g. <m name="italic"><string value="Hi
there!"/></m>). Arguments to markup commands may be other commands, or other
objects (markup \score even has a score argument, which is also supported).


Example:

This LilyPond music:

  \relative {
    c d e
  }

maps to Scheme (using \displayMusic):

  (make-music
    'RelativeOctaveMusic
    'element
    (make-music
      'SequentialMusic
      'elements
      (list (make-music
              'NoteEvent
              'pitch
              (ly:make-pitch -1 0 0)
              'duration
              (ly:make-duration 2 0 1))
            (make-music
              'NoteEvent
              'pitch
              (ly:make-pitch -1 1 0)
              'duration
              (ly:make-duration 2 0 1))
            (make-music
              'NoteEvent
              'pitch
              (ly:make-pitch -1 2 0)
              'duration
              (ly:make-duration 2 0 1)))))

and maps to XML (using \displayLilyXML):

  <music name="RelativeOctaveMusic">
    <origin filename="/home/wilbert/dev/python-ly/ly/xml/xml-export.ily" line="244" char="17"/>
    <element>
      <music name="SequentialMusic">
        <origin filename="/home/wilbert/dev/python-ly/ly/xml/xml-export.ily" line="244" char="27"/>
        <elements>
          <music name="NoteEvent">
            <origin filename="/home/wilbert/dev/python-ly/ly/xml/xml-export.ily" line="245" char="4"/>
            <pitch octave="-1" notename="0" alteration="0"/>
            <duration log="2" dots="0" numer="1" denom="1"/>
          </music>
          <music name="NoteEvent">
            <origin filename="/home/wilbert/dev/python-ly/ly/xml/xml-export.ily" line="245" char="6"/>
            <pitch octave="-1" notename="1" alteration="0"/>
            <duration log="2" dots="0" numer="1" denom="1"/>
          </music>
          <music name="NoteEvent">
            <origin filename="/home/wilbert/dev/python-ly/ly/xml/xml-export.ily" line="245" char="8"/>
            <pitch octave="-1" notename="2" alteration="0"/>
            <duration log="2" dots="0" numer="1" denom="1"/>
          </music>
        </elements>
      </music>
    </element>
  </music>

To automatically export a full LilyPond document to an XML representation,
use the xml-export-init.ly script with the --init LilyPond option. That script
automatically sets up LilyPond to output one XML document with a <document>
root element, containing a <book> element for every book in the LilyPond file.
(LilyPond always creates at least one book, collecting all the music or markup
at the toplevel.)

%}

% convert an assoc list to an xml attribute string (joined with a space in between)
#(define (attrs->string attrs)
   (string-join
    (map (lambda (e)
           (attr->string (car e) (cdr e))) attrs)
    " " 'prefix))

% convert a name value pair to an xml attribute
% name is a symbol, value can be a symbol, string, or number
#(define (attr->string name value)
   (string-append (symbol->string name)
     "=\""
     (cond
      ((string? value) (attribute-escape value))
      ((number? value) (number->string value))
      ((symbol? value) (attribute-escape (symbol->string value))))
     "\""))

% escape string for xml body
#(define (xml-escape s)
   (ly:string-substitute "<" "&lt;"
     (ly:string-substitute ">" "&gt;"
       (ly:string-substitute "\"" "&quot;"
         (ly:string-substitute "&" "&amp;"
           s)))))

% escape string for xml attribute
#(define (attribute-escape s)
   (ly:string-substitute "\n" "&#10;"
     (ly:string-substitute "\"" "&quot;"
       (ly:string-substitute "&" "&amp;"
         s))))


% a nice class that outputs an XML document
% (define x (XML port)  ;; port is optional
% (x 'open-tag 'name attrs)
% (x 'open-close-tag 'name attrs)
% (x 'close-tag)
% when an open tag is closed and it has no child tags, it is automatically
% written to output as an open-close tag.
#(define XML
   (lambda args
     (define indent-width 2)
     (define pending #f)
     (define tags '())
     (define port (if (pair? args) (car args) (current-output-port)))

     (define (output-xml-tag indent tag-name attrs text how)
       "output an XML tag.
           indent: number of spaces before it
           tag-name: symbol
           attrs: assoc list
           text: text between open and close tag (how must be 'text-tag)
           how can be:
            'open-tag:       write an open-tag with attributes <element bla=\"blabla\">
            'close-tag:      write a close-tag (attrs are ignored) </element>
            'open-close-tag: write a self-closing tag <element bla=\"blabla\"/>
            'text-tag:       write a open and close tag with text <el bla=\"blabla\">text</el>
       "
       (let ((s (string-append
                 (make-string (* indent indent-width) #\space)
                 "<"
                 (if (eq? how 'close-tag) "/" "")
                 (symbol->string tag-name)
                 (if (eq? how 'close-tag) "" (attrs->string attrs))
                 (if (eq? how 'open-close-tag) "/" "")
                 ">"
                 (if (eq? how 'text-tag)
                     (string-append (xml-escape text) "</" (symbol->string tag-name) ">")
                     "")
                 "\n")))
         (display s port)))
     
     (define (output-last-tag how)
       "output the last tag on the tags stack."
       (let ((indent (1- (length tags)))
             (args (car tags)))
         (apply (lambda (tag-name attrs)
                  (output-xml-tag indent tag-name attrs "" how))
           args)))

     (define (declaration)
       "output an XML declaration."
       (display "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n" port))

     (define (open-tag tag-name attrs)
       "implementation of open-tag method."
       (if pending
           (output-last-tag 'open-tag))
       (set! tags (cons (list tag-name attrs) tags))
       (set! pending #t))

     (define (close-tag)
       "implementation of close-tag method."
       (if pending
           (output-last-tag 'open-close-tag)
           (output-last-tag 'close-tag))
       (set! pending #f)
       (set! tags (cdr tags)))

     (define (text-tag tag-name text attrs)
       "implementation of text-tag method."
       (if pending
           (output-last-tag 'open-tag))
       (output-xml-tag (length tags) tag-name attrs text 'text-tag)
       (set! pending #f))

     (lambda (method-name . args)
       "call a method. 
          'declaration
          'open-tag tag-name [attrs]
          'close-tag
          'open-close-tag tag-name [attrs]
          'text-tag tag-name text [attrs]
      "
       (let* ((l (length args))
              (tag-name (if (> l 0) (list-ref args 0)))
              (text (if (and (> l 1) (string? (list-ref args 1))) (list-ref args 1) ""))
              (attrs (if (and (> l 1) (list? (list-ref args (1- l)))) (list-ref args (1- l)) '())))
         (case method-name
           ((declaration) (declaration))
           ((open-tag) (open-tag tag-name attrs))
           ((close-tag) (close-tag))
           ((open-close-tag) (open-tag tag-name attrs) (close-tag))
           ((text-tag) (text-tag tag-name text attrs)))))))


% convert a markup object to XML
#(define (markup->lily-xml mkup xml)

   (define (cmd-name proc)
     "return the name of the markup procedure"
     (symbol->string (procedure-name proc)))

   (define (mkuparg->xml arg)
     "convert markup arguments to xml"
     (cond
      ((markup-list? arg) ;; markup list
        (for-each mkup->xml arg))
      ((markup? arg) ;; markup
        (mkup->xml arg))
      (else ;; can be another scheme object
        (obj->lily-xml arg xml))))

   (define (mkup->xml mkup)
     "convert a markup object to xml"
     (if (string? mkup)
         (xml 'text-tag 'string mkup)
         (begin
          (xml 'open-tag 'm `((name . ,(cmd-name (car mkup)))))
          (for-each mkuparg->xml (cdr mkup))
          (xml 'close-tag))))

   ;; wrap markup in a toplevel <markup> tag
   (xml 'open-tag 'markup)
   (mkuparg->xml mkup)
   (xml 'close-tag))


% convert a header to XML
#(define (header->lily-xml header xml)
   (if (module? header)
       (let ((variables
              (filter (lambda (v)
                        (not (eq? (car v) '%module-public-interface))) (ly:module->alist header))))
         (if (pair? variables)
             (begin
              (xml 'open-tag 'header)
              (for-each (lambda (v)
                          (xml 'open-tag 'variable `((name . ,(car v))))
                          (obj->lily-xml (cdr v) xml)
                          (xml 'close-tag)) variables)
              (xml 'close-tag))))))


% convert any object to XML
% currently the xml is just (display)ed but later it will be written to a file or string.
% xml is an XML instance
#(define (obj->lily-xml o xml)
   (cond
    ((ly:music? o)
     (let ((name (ly:music-property o 'name))
           (e (ly:music-property o 'element))
           (es (ly:music-property o 'elements))
           (as (ly:music-property o 'articulations))
           (tw (ly:music-property o 'tweaks))
           (location (ly:music-property o 'origin))
           (pitch (ly:music-property o 'pitch))
           (duration (ly:music-property o 'duration))
           (properties
            (filter
             (lambda (prop)
               (not (memq (car prop)
                      '(name element elements articulations tweaks origin pitch duration))))
             (ly:music-mutable-properties o)))
           )
       (xml 'open-tag 'music `((name . ,name)))
       (if (ly:input-location? location)
           (obj->lily-xml location xml))
       (if (ly:pitch? pitch)
           (obj->lily-xml pitch xml))
       (if (ly:duration? duration)
           (obj->lily-xml duration xml))
       (if (ly:music? e)
           (begin
            (xml 'open-tag 'element)
            (obj->lily-xml e xml)
            (xml 'close-tag)))
       (if (and (list? es) (not (null? es)))
           (begin
            (xml 'open-tag 'elements)
            (for-each (lambda (e)
                        (obj->lily-xml e xml)) es)
            (xml 'close-tag 'elements)))
       (if (and (list? as) (not (null? as)))
           (begin
            (xml 'open-tag 'articulations)
            (for-each (lambda (e)
                        (obj->lily-xml e xml)) as)
            (xml 'close-tag 'articulations )))
       (if (and (list? tw) (not (null? tw)))
           (begin
            (xml 'open-tag 'tweaks)
            (for-each (lambda (e)
                        (obj->lily-xml e xml)) tw)
            (xml 'close-tag 'tweaks)))
       (for-each (lambda (prop)
                   (xml 'open-tag 'property `((name . ,(car prop))))
                   (obj->lily-xml (cdr prop) xml)
                   (xml 'close-tag)) properties)
       (xml 'close-tag)))

    ((ly:moment? o)
     (xml 'open-close-tag 'moment
       `((main-numer . ,(ly:moment-main-numerator o))
         (main-denom . ,(ly:moment-main-denominator o))
         (grace-numer . ,(ly:moment-grace-numerator o))
         (grace-denom . ,(ly:moment-grace-denominator o)))))
    ((ly:input-location? o)
     (let ((origin (ly:input-file-line-char-column o)))
       (xml 'open-close-tag 'origin
         `((filename . ,(car origin))
           (line     . ,(cadr origin))
           (char     . ,(caddr origin))))))
    ((ly:pitch? o)
     (xml 'open-close-tag 'pitch
       `((octave . ,(ly:pitch-octave o))
         (notename . ,(ly:pitch-notename o))
         (alteration . ,(ly:pitch-alteration o)))))
    ((ly:duration? o)
     (xml 'open-close-tag 'duration
       `((log . ,(ly:duration-log o))
         (dots . ,(ly:duration-dot-count o))
         (numer . ,(car (ly:duration-factor o)))
         (denom . ,(cdr (ly:duration-factor o))))))
    ((markup-list? o)
     (markup->lily-xml o xml))
    ((and (markup? o) (not (string? o)))
     (markup->lily-xml o xml))
    ((number? o)
     (xml 'text-tag 'number (number->string o)))
    ((string? o)
     (xml 'text-tag 'string o))
    ((char? o)
     (xml 'text-tag 'char (string o)))
    ((boolean? o)
     (xml 'text-tag 'boolean (if o "true" "false")))
    ((symbol? o)
     (xml 'text-tag 'symbol (symbol->string o)))
    ((null? o)
     (xml 'open-close-tag 'null)) ; or <list/> ??
    ((list? o)
     (begin
      (xml 'open-tag 'list)
      (for-each (lambda (e)
                  (obj->lily-xml e xml)) o)
      (xml 'close-tag)))
    ((pair? o)
     (begin
      (xml 'open-tag 'pair)
      (obj->lily-xml (car o) xml)
      (obj->lily-xml (cdr o) xml)
      (xml 'close-tag)))
    ((procedure? o)
     (let* ((name (procedure-name o))
            (attrs (if name `((name . ,name)) '()))
            (source (procedure-source o)))
       (xml 'open-tag 'procedure attrs)
       (if source
           (begin
            (xml 'open-tag 'procedure-source)
            (obj->lily-xml source xml)
            (xml 'close-tag)))
       (xml 'close-tag)))
    ((ly:stencil? o)
     (begin
      (xml 'open-tag 'stencil
        `((x-min . ,(car (ly:stencil-extent o X)))
          (x-max . ,(cdr (ly:stencil-extent o X)))
          (y-min . ,(car (ly:stencil-extent o Y)))
          (y-max . ,(cdr (ly:stencil-extent o Y)))))
      (obj->lily-xml (ly:stencil-expr o) xml)
      (xml 'close-tag)))
    ((ly:score? o)
     (begin
      (xml 'open-tag 'score)
      (header->lily-xml (ly:score-header o) xml)
      (obj->lily-xml (ly:score-music o) xml)
      (xml 'close-tag)))
    ((ly:book? o)
     (begin
      (xml 'open-tag 'book)
      (header->lily-xml (ly:book-header o) xml)
      (for-each (lambda (book)
                  (obj->lily-xml book xml))
        (reverse (ly:book-book-parts o)))
      (for-each (lambda (score)
                  (obj->lily-xml score xml))
        (reverse (ly:book-scores o)))
      (xml 'close-tag)))

    ))


#(define-public (xml-export obj)
   "Dump an XML representation of the specified object to the current output port."
   (let ((xml (XML)))
     (xml 'declaration)
     (obj->lily-xml obj xml)))


displayLilyXML = #
(define-music-function (parser location music) (ly:music?)
  "Dump an XML representation of the music to the current output port."
  (xml-export music)
  music)


