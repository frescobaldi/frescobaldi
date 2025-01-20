=== Editor Preferences ===

= Highlighting Options =

Here you can define how long "matching" items like matching brackets or the 
items linked through Point-and-Click are highlighted.

Use the value 0 for infinite.


= Indenting Preferences =

Here you can specify how you want to handle Tabs and indenting.

The entry *Tab Width* specifies the visual distance between tab stops. It 
does not change the indenting behaviour or the document contents.

Using the entry *Indent with* you can specify how many spaces will be 
inserted it you press Tab once at the beginning of the line, or when you 
press enter after a character that starts a new level of indent
(and {menu_autoindent} is enabled).

By default 2 spaces are inserted, but you can move the number to zero to use 
a literal Tab character for every level of indent.

The entry *Tab outside indent inserts* specifies what happens when you press 
Tab while in the middle of a line of text. Also here you can choose to insert
a real Tab by moving the number to zero.

You can also set indentation preferences per-document, see
{document_variables}.

= Source Export Preferences=

Configures how colored source code is produced when exporting to a file or
copying to clipboard. Available options are:

* `Copy HTML as plain text` |
  Generates the colored source code as HTML markup so it can be pasted in HTML
  pages.  When unchecked rich text is produced that can be pasted to rich text
  editors like word processors.
* `Copy document body only` |
  Wraps the source in a single HTML tag. When unchecked a full HTML document is
  produced.
  *Note:* This option doesn't take effect when *exporting* source code.
* `Use inline style when copying colored HTML` |
  Inserts CSS styles *in* the generated HTML tags.
  When unchecked CSS classes are used.
  *Note:* When this option is *unchecked* and `Copy document body only` is
  *checked* no actual CSS styles will be generated. To use this option there has
  to be an external CSS available in the target document.
  *Note:* This option doesn't take effect when *exporting* source code.
* `Use inline style when exporting colored HTML` |
  Same as above but applies for exporting instead of copying.
* `Show line numbers` |
  (should be self-explanatory)
* `Wrappers` |
  By default colored code is wrapped in a `<pre id="document"></pre>` tag, but
  this can be configured to use a selection of wrapper tags and attribute types
  and an arbitrary attribute name.
  So it is for example to generate an `<div class="lilypond">` element if that
  is more suitable for the existing CSS.


#VARS
menu_autoindent menu tools -> submenu title|Code &Formatting -> &Automatic Indent
document_variables help docvars

#SEEALSO
indent_format
