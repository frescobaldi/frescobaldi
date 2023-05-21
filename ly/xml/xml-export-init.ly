%{

This script is intended to be used via the --init option. It automatically converts
every \book in the score to an XML document (LilyPond always creates at least one book).
In this case the XML is also written to standard output, but you can specify another file
with -dxml-export=<filename>.

So, to convert a LilyPond source file to an XML file containing the LilyPond music
structure in XML format, use the following command:

  lilypond --init /path/to/xml-export-init.ly -dxml-export=song.xml song.ly

The XML document has a <document> root element, containing a <book> element for every book
in the LilyPond file.

%}

%% find our companion script, but leave the old setting of relative-includes
#(define old-option-relative-includes (ly:get-option 'relative-includes))
#(ly:set-option 'relative-includes #t)
\include "xml-export.ily"
#(ly:set-option 'relative-includes old-option-relative-includes)

%% make a toplevel book handler
#(define (make-toplevel-book-handler->xml xml)
   "Return a book handler that dumps a book to specified XML instance"
   (lambda (parser book)
     (obj->lily-xml book xml)))

%% create the XML output instance (in the toplevel scope)
#(begin
  (define xml-outputter #f)
  (let* ((x (ly:get-option 'xml-export))
         (xml-file (if x (symbol->string x) "-"))
         (port (if (string=? xml-file "-")
                   (current-output-port)
                   (open-output-file xml-file)))
         (xml (XML port)))
    (ly:message
     (format "Writing XML to ~a..."
       (if (string=? xml-file "-")
           "standard output"
           xml-file)))
    (set! xml-outputter xml)))

%% create the output document and run the normal init procedure
#(xml-outputter 'declaration)
#(xml-outputter 'open-tag 'document)
%% HACK, overwrite print-book-with-defaults, because toplevel-book-handler
%% is overwritten by the declarations-init.ly script.
#(define print-book-with-defaults (make-toplevel-book-handler->xml xml-outputter))
\include "init.ly"
#(xml-outputter 'close-tag)
#(ly:message "Writing XML completed.")
