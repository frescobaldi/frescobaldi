=== Python Snippets ===

Python snippets can read and should set the variable `text`.
The variable `text` contains the currently selected text (which may be an
empty string).
        
You may set `text` to a string or a list of strings.

Other variables that may be referenced:

!`state`
: A list of strings describing the type of text the cursor is at.

!`cursor`
: The current QTextCursor, giving access to the document.
  Don't change the document through the cursor, however.

!`CURSOR`
: When setting `text` to a list instead of a string, you can use this value to
  specify the place the text cursor will be placed after inserting the snippet.

!`ANCHOR`
: When setting `text` to a list instead of a string, this value can be used
  together with `CURSOR` to select text when inserting the string parts of
  the list.

!`main`
: When you define a function with this name, it is called without arguments,
  instead of inserting the text from the `text` variable. In this case you 
  may alter the document through the `cursor`.

