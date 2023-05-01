README for Frescobaldi
======================

Homepage: http://www.frescobaldi.org/
Main author: Wilbert Berendsen

Frescobaldi is a LilyPond sheet music text editor. It aims to be powerful, yet
lightweight and easy to use. Frescobaldi is Free Software, freely available
under the General Public License.

Features:

- Powerful text editor with syntax highlighting and automatic completion
- Music view with advanced two-way Point & Click
- Midi player to proof-listen LilyPond-generated MIDI files
- Midi capturing to enter music
- Powerful Score Wizard to quickly setup a music score
- Snippet Manager to store and apply text snippets, templates or scripts
- Use multiple versions of LilyPond, automatically selects the correct version
- Built-in LilyPond documentation browser and built-in help
- Configurable document outline view to navigate large LilyPond scores easily
- Smart layout-control functions like coloring specific objects in the PDF
- Import ABC, Midi and MusicXML using the LilyPond-provided tools
- Experimental export to MusicXML
- Modern user interface with configurable colors, fonts and keyboard shortcuts
- Translated into: Dutch, English, French, German, Italian, Swedish, Czech,
  Russian, Spanish, Galician, Turkish, Polish, Brazilian, Ukrainian,
  Traditional Chinese, Simplified Chinese and Japanese.

Music functions:

- Transpose music
- Change music from relative to absolute and vice versa
- Change the language used for note names
- Change the rhythm (double, halve, add/remove dots, copy, paste) etc
- Hyphenate lyrics using word-processor hyphenation dictionaries
- Add spanners, dynamics, articulation easily using the Quick Insert panel
- Update LilyPond syntax using convert-ly, with display of differences

Frescobaldi is designed to run on all major operating systems (Linux, Mac OS X
and MS Windows). It is named after Girolamo Frescobaldi (1583-1643), an Italian
composer of keyboard music in the late Renaissance and early Baroque period.

Here is an idea of the basic Frescobaldi workflow:

- Start Frescobaldi
- Open a .ly file or create one using *File->New* from template or
  *Tools->Setup new Score...* and fill in some music
- Press Ctrl+M to run LilyPond
- If the LilyPond output shows errors, press Ctrl+E to jump to the first error
- If you see other mistakes in the music, click the notes to move the text
  cursor there
- Fix the errors or mistakes in the text
- Press Ctrl+M again to update the music view
- When a piece is finished, press Ctrl+Shift+P once to run LilyPond with point
  and click turned off (this results in a much smaller PDF file).

Frescobaldi is written in Python and uses PyQt for its user interface.

Installation instructions for the program and MIDI support as well as other
information can be found in the [Wiki](https://github.com/frescobaldi/frescobaldi/wiki).
Other requirements and installation instructions may also be found in the
[INSTALL.md](INSTALL.md) file.
