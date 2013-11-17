=== Pitch Manipulation ===


Frescobaldi offers the following pitch-manipulating functions,
all in the menu {menu}:

Pitch language
: This translates pitch names in the whole document or a selection.

Convert relative music to absolute
: This converts all `\relative` music parts to absolute pitch names.
  It removes, but honours, octave checks.

Convert absolute music to relative
: Checks all toplevel music expressions, changing them into
  `\relative` mode as soon as the expression contains a pitch.
  If you want to make separate sub-expressions relative, it may be necessary to
  select music from the first expression, leaving out higher-level opening
  braces.



#SUBDOCS
transpose
modal_transpose

#VARS
menu menu tools -> submenu title|&Pitch
