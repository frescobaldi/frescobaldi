=== Configuring the Outline View ===
    
The document outline view is created by looking for certain expressions in 
the document text.

You can specify what to search for by entering a list of regular expressions.

In those expressions, `^` matches at the beginning of every line, and `$` 
matches at the end of a line.

Normally when an expressions matches text, the whole match is displayed as 
an item in the outline.

You can also use named groups, with the {code} named group syntax.

You can use the name `text` or `title`. In that case, only the named part of 
a match is displayed. If the `title` name is used, it is displayed in a bold 
font.

For more information about regular expressions, see {link}.


#VARS
code md `(?P<name>`...
link help search_replace

