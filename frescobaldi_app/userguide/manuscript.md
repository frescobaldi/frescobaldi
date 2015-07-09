=== Manuscript Viewer ===

The *Manuscript Viewer* can be used to have the to-be-copied score open in
Frescobaldi.  Initially this is a simple tool that can only display single PDF
files, but the viewer will be significantly enhanced to become a powerful
editorial tool.

Navigating is currently possible with the scroll bars and by dragging the image
with the mouse, and zooming can be achieved with *Ctrl* and the mouse wheel.
*Ctrl*-clicking accesses the magnifyer as with the {music_view}.

=== Roadmap ===

This is an initial release. Among the planned features of the manuscript viewer are:

* Link manuscripts to score documents (so manuscripts are opened automatically
  if available)
* Manage multiple manuscripts per score document
* Let the user define a "grid" to maintain information about where the measures
  are in the manuscript.
* Automatically link the cursor position with the corresponding place in the
  manuscripts.
* Allow the user to compare the "current" measure in the different manuscripts
* Let LilyPond use the manuscripts' breaking for compilation so the engraved score's
  page layout always matches the currently visible manuscript.

  #VARS
  music_view help musicview
