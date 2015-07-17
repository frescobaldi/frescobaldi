=== Manuscript Viewer ===

The *Manuscript Viewer* can display PDF documents alongside the default
{music_view}. Typically it is used to have the to-be-copied manuscript(s) open
in Frescobaldi's window (that's where the tool got its name from) but it can
also be useful to show arbitrary documents, for example with notes or task
descriptions.  

One or more manuscripts can be opened using the *Open* button, new files are
added to the list of open manuscripts. The current manuscript can be closed
with the *Close* button, and there are context menu entries to close all other
or all manuscripts.  The opened manuscripts are maintained in sessions, alongside
the input documents.

Navigation, zooming and printing provide the same functionality as the {music_view}
tool, giving access through buttons, context menu items and mouse interaction.

It is possible to inspect the document with the magnifying glass by *Ctrl*-clicking,
and upon drawing a selection rectangle with the right mouse key (*Ctrl-click-drag
on Mac*) an excerpt from the document can be exported to a PNG file.

If the opened file is a PDF score engraved by LilyPond and containing valid
point-and-click links several function of {music_view} also work in the
manuscript viewer:

* Highlight input by selecting music or vice versa
* Move the viewer to the current cursor position
* Synchronize the document cursor with the view (automatic following)
* Edit in place

However, when that score should be recompiled wtih LilyPond the manuscript viewer
won't automatically update, but this can be done manually through the context
menu

If a manuscript contains external hyperlinks they can be clicked on and will
open in an external viewer/browser. This may be practical for keeping lists of
useful links around in that window.


=== Roadmap ===

This is an initial release. Among the planned features of the manuscript viewer are:

* Maintain a *set* of manuscripts to an input document. Let the set be opened
  automatically.
* Edit metadata for that set of manuscripts, making the viewer an editorial
  tool for scholarly editions.
* Automatically link the cursor position with the corresponding place in the
  manuscripts. (The user will have to mark up the manuscripts for this to work.)
* Display the "current" measure in the different manuscripts
* Let LilyPond use the manuscripts' breaking for compilation so the engraved score's
  page layout always matches the currently visible manuscript.

#VARS
music_view help musicview
