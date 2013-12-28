=== Document Variables ===

Document variables are variables that influence the behaviour of Frescobaldi.
They can be written in the first five or last five lines of a document.
If a line contains '`-*-`', Frescobaldi searches the rest of
the lines for variable definitions like `name: value;`.

The following variables are recognized:

= General variables =

!`mode: _(mode)_;`
: Force mode to be one of lilypond, html, texinfo, latex,
  docbook or scheme. Default: automatic mode recognition.
  
!`master: _(filename)_;`
: Compiles another LilyPond document instead of the current.

!`output: _(name)_;`
: Looks for output documents (PDF, MIDI, etc.) starting with
  the specified name or comma-separated list of names.
  [var_output More information].

!`coding: _(encoding)_;`
: Use another encoding than the default UTF-8.

!`version: _(version)_;`
: Set the LilyPond version to use, can be used for non-LilyPond documents.

= Indentation variables =

!`tab-width: _(number)_;`
: The visible width of a tab character in the editor, by default 8.

!`indent-tabs: yes/no;`
: Whether to use tabs in indent, by default {no}.

!`indent-width: _(number)_;`
: The number of spaces each indent level uses, by default 2.
  This value is ignored when `indent-tabs` is set to {yes}.

!`document-tabs: yes/no;`
: Whether to use tabs elsewhere in the document, by default {no}.

!`document-tab-width: _(number)_;`
: How many spaces to insert when Tab is pressed in the middle of text,
  by default 8. This value is ignored when `document-tabs` is set to {yes}.



#SUBDOCS
var_output

#VARS
no md `no`
yes md `yes`

#L10N
do not translate the mode names lilypond, html, etc.

