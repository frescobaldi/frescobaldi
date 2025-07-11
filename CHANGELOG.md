<!-- Please follow this spec: https://keepachangelog.com/
[X.Y.Z] links to the GitHub list of commits in a tag/release are
defined at the bottom of this file.
-->
# Changelog

All notable changes to the Frescobaldi project are documented in this file.
Click on the version to see the complete list of commits in a release.

## [unreleased]

## [4.0.3] - 2025-06-09

### Fixed

- MIDI playback on macOS works again, thanks to the switch to
the Pygame Community Edition fork (#1987).
- #1956 issue ("TypeError: 'NoneType' object is not callable"),
reported by several users, has been fixed in #1959.
- Some minor fixes: #1955, #1961, #1967, #1974, #1977, #1984.

### Changed

- Select an appropriate default editor font for each platform: Consolas for Windows; SF Mono, Menlo or Monaco for macOS; the system monospace default for Linux (#1960).
- Add a keyboard shortcut `Ctrl+,` to open the Preferences in any operating system (#1952).
- Updated translations: German, Japanese, Polish.

### Added

- Add Qt version check (#1938). Frescobaldi won't run if the installed
Qt version is below the required version number.


## [4.0.2] - 2025-05-06

### Changed

- Reorganize and extend the Preferences (#1920 and #1928).
- Use hatchling as build backend (#1913).
- Updated translations: Italian, Polish.

### Fixed

- Make MIDI input work again (#1919 and #1922).
- Fix a garbage-collector issue (#1935 and #1942). This should prevent
the error "RuntimeError: wrapped C/C++ object of type FOO has been deleted",
which has been reported as duplicates several times.


## [4.0.1] - 2025-04-03

### Fixed

- Fixed two annoying crashes on macOS (#1868 and #1897) by updating
  packages to PyQt 6.8.1.
- Fixed Python wheel packaging issues in #1901. This is relevant
  especially for Linux package maintainers.
- Bold fonts are now supported in Windows (#1902).


## [4.0.0] - 2025-03-29

### Changed

- Ported to PyQt6 (requires Qt >=6.6) (#1780).
- Moved to current Python packaging tools (#1597, #1638).
- Use standard gettext module (#1620).
- Windows and macOS packages are now built with Briefcase (#1859 and #1887).
- Updated translations: French, German, Italian and Polish.

### Added

- Automatic installation of LilyPond (#1655).
- Score Wizard improvements (#1690).
- Korean translation (#1623).

### Fixed

- Docking/undocking panels on Wayland (Linux) is working again thanks to the Qt6 port.
- Several minor bug fixes.


## [3.3.0] - 2023-03-26

### Added

- Score Wizard improvements: the MIDI instrument is now user-selectable
  for several keyboard and guitar part types; new part types for steelpan and
  dulcimer; new special "Structure" type for laying out breaks, bar lines,
  etc. separately from musical content. (#1375)
- Add option to format on save (#1473)
- Make all layout control options compatible with LilyPond 2.24 (#1489)
- Default URLs to browse the documentation of LilyPond stable and unstable (#1538)
- Updated translations: French, Italian and Japanese

### Fixed

- Linux: display application icon on Wayland (#1478)
- Fix crash at startup when using Python >=3.11 (#1480)
- Ignore inactive code in the Outline (#1482)
- Fix cursor column position (#1517)
- Small fixes to the behaviour of "Go to line number" (#1523)
- Improve selection behavior in list of snippets (#1535)
- Fix error when changing the application language in the preferences (#1540)
- Linux: fix menus sometimes detached from its parent on Wayland (#1541)
- Ignore never-saved files when reloading (#1542)
- Fix extraneous document when opening new file from the command line (#1556)
- Fix internal error when trying to compile a file without having
  LilyPond installed (#1567)

### Changed

- Require Python 3.8 (#1519)
- Make bug reports sent via GitHub instead of by email (#1559)
- Always respect the shebangs of LilyPond's Python scripts on macOS
  and remove the corresponding configuration option (#1565)

### Removed

- Remove "Display control points" layout option (#1474)


## [3.2] - 2022-05-05

### Added

- New preference feature: music view preference for "Strict Paging": when
  enabled, the pageup/pagedown keys always page to the previous or next page
  instead of simply scrolling a screenful.
- Improvements to the Score Wizard, contributed by Benjamin Johnson (#1343):
  - Various new instruments, mostly guitar, synth and bass related
  - New command File->New->Score Wizard from current document, which reads some
    properties and score setup from the current document.
- Translations:
  - some missing strings from Qt dialogs were added (WB, #1224)
  - new Japanese translation by Jun Tamura, thanks!
  - updates: Dutch, Italian and Russian

### Fixed

- Many small fixes to make Frescobaldi work with Python 3.10, where no floating
  point values may be given to functions that require an integer argument.
- Fixed a crash when a main window was closed (often on Mac OS X) (#1427)

### Changed

- the qpageview module, thus far in frescobaldi_app/qpageview, is now,
  because of its generic nature, a separate project at
  http://github.com/frescobaldi/qpageview . This package needs to be
  installed for Frescobaldi to work; it is used by the Music View and other
  viewers inside Frescobaldi. Because of this, be sure to remove Frescobaldi
  completely and then install qpageview and Frescobaldi, otherwise it still
  finds the old qpageview inside the frescobaldi_app folder.


## [3.1.3] - 2020-12-26

### Added

- new Clear music view button and menu action (wish #1235)
- Translation updates: Dutch, Russian, Czech.

### Fixed

- fixed #1311 "NameError: name 'imp' is not defined" when importing
- fixed search of generated files on macOS for some Unicode file names
- fixed selection of Python on macOS:
  - select the system Python 2 or 3 according to LilyPond's version
  - support MacPorts' LilyPond tools
  - add option to allow forcing the use of the tools' #! lines
    (useful for self-compiled or other nonstandard LilyPond installations)
- fixed #1305 Ghostscript error on Mac with MacPorts' LilyPond 2.21.x



## [3.1.2] - 2020-04-13

### Added

- add DE hyphen patterns and copyright info (#1275)
- updated translations: Dutch, Italian

### Fixed

- fixed #1255, AttributeError: 'NoneType' object has no attribute 'cursor'
- fixed "Two Pages (first page right)" for both modes, other should be "left"
- fixed pinch gesture zoom in music view on Mac
- fixed #30, Printing score under Mac OS X
- fixed #860, OSX: Frescobaldi overrides critical cursor navigation keyboard shortcuts;
  new shortcuts:
  - next document: ctrl+tab
  - previous document: ctrl+shift+tab
  - start of line: cmd+left
  - end of line: cmd+right
- fixed #1087, File names in document tabs are not shown correctly on Mac
- fixed #1272, Global menu with no windows on Mac is not working
- fixed #1232, Error using convert-ly in Frescobaldi 3.1 Mac app

### Changed

- The userguide now has its own PO files in i18n/userguide, and the
Frescobaldi application itself has the PO files in i18n/frescobaldi, see
[TRANSLATIONS.md](TRANSLATIONS.md).


## [3.1.1] - 2020-01-04

### Fixed

- fixed #1242, AttributeError: 'PopplerDocument' has no attribute 'ispresent'
- fixed #1234, NameError: 'QPinchGesture' is not defined (pinch in music view)
- fixed #1231, NameError: 'doc' is not defined (when printing on Mac OSX)


## [3.1] - 2019-12-27

### Changed

- Frescobaldi now requires Python3.3+
- Userguide now has its own PO files. PO files for userguide and Frescobaldi
  both are in 'i18n/xx_CC' directories, see [TRANSLATIONS.md](TRANSLATIONS.md).

### Added

- New "Document Fonts" dialog supporting text and music fonts
  and providing a font sample previewer
- Possibility to load external extensions
- New "First System Only" option in Custom Engrave
- Goto Line command (#927, feature request #676)
- Rename file command (#1057, feature request #980)
- Music view:
  - Copy to Image can copy/export to SVG, PDF and EPS in addtion to PNG/JPG
  - New toolbar button to show/hide the magnifier
  - New preference Horizontal / Vertical
  - New preference Continuous / non-continuous (displays only current page(s))
  - New commands to rotate left / right
  - New raster layout mode (displays as many pages as fit in a View)
  - View settings are remembered per-document
- Manuscript viewer:
  - Toolbar buttons to rotate the pages left / right
  - New toolbar button to show/hide the magnifier
- Translations: updated Dutch and Italian

### Fixed

- fixed #895 seeking in MIDI player during playing stops sound
- fixed #768, now paper orientation is properly handled in New Score Wizard
- fixed #705, discrepancy of LilyPond vs. system version of GhostScript
  on Linux (#926)
- fixed #1094, includepaths on Windows (#1095)
- fixed #1121, NameError: name 'widgets' is not defined

### Improvements

- Score Wizard: Titles and Headers are shown in preview (#1216)
- Score Wizard: checkbox to write/omit pitches after \relative command
- Score Wizard: allow "none" for instrument names on first system (#1141)
- Smarter behaviour of the autocompletion popup (#918, #922)
- New command File->Rename/Move... (#980)
- Sessions can be grouped in the Sessions menu
- Show absolute path of include files in tooltip (#941)
- Restructure Tools Menu (#1080)
- File Open toolbar button shows recent files menu on long click
- Added "Blank Sheet Music" template snippet (#1139)

### Internals

- Multithreaded Job Queue preparing multicore support (#1103)
- Rewrite code handling external processes/jobs (#1100)
- Music (pre)views could previously only display PDF documents; this has been
  rewritten so that many more formats can be displayed like SVG and images,
  which will open up new possibilities for the music view and the manuscript
  viewer (#1202)
- The SVG view and the LilyPond documentation browser now use QtWebEngine
  instead of the deprecated QtWebKit


## [3.0.0] - 2017-02-17

### Added

- Zoom with pinch gesture in Music View, contributed by David Rydh
- An option (enabled by default) to move the cursor to the end of the line
  when PageDown is pressed on the last line, and to move the cursor to the
  start of the first line if PageUp is pressed on the first line
- Retina display support in Music View, contributed by David Rydh

### Changed

- Frescobaldi now requires Python3.2+, Qt5, PyQt5, python-poppler-qt5

<!-- 2.x.y releases (using old ChangeLog format) -->

## 2.20.0 -- February 17th, 2017

* New features:
  - New Manuscript viewer tool, displaying an "engraver's copy",
    contributed by Peter Bjuhr and Urs Liska
  - Copy selected text in Music View
  - New command Edit->Move to include file...
  - New quick remove actions to remove beams and ligatures from selected music
  - Search tool in the keyboard shortcuts preferences page (#690)
* Improvements:
  - Fit Width in Music View now fits two pages in width, if in two-page mode
  - the Music View now remembers the page layout mode
  - Jump to next or previous bookmark now respects surrounding lines setting
  - Better default save path, looking at last edited document (#162)
* Bug fixes:
  - fix #716 position of open document tab bar changes on engrave
  - Midi input fixes by David Rydh:
    * fix #797 and #853, now honour Midi input port setting
    * in Midi input, ces and bis now have the correct octave
    * fix interruption of Midi input by other events than note events
  - Midi input now uses correct channel, fix by David Kastrup
  - fix #857 UnicodeDecodeError on some types of \displayMusic command output
  - fix #891 QTextBlock not hashable anymore
  - fix #862 midi not loaded on first document load
* Translations:
  - new Swedish translation contributed by Dag Odenhall
  - updated Dutch by Wilbert Berendsen
  - updated Italian by Federico Bruni
  - updated Spanish by Francisco Vila
  - updated German by Henning Hraban Ramm
  - updated Czech by Pavel Fric


## 2.19.0 -- April 22nd, 2016

* Requirement changes:
  - Frescobaldi now requires python-ly 0.9.4
* New features:
  - Tools->Quick Remove->Remove Fingerings
  - Tools->Quick Remove->Remove Comments
  - Tools->Pitch->Simplify Accidentals
  - It is now configurable whether the document tabs have a close button
  - The new LilyPond feature to embed source code files in the PDF (LilyPond >=
    2.19.39) can be used in publish mode and the custom engrave dialog (#813)
  - Clicking a TOC item in the Music View jumps to its destination (#803)
  - When copying music to an image, a new option has been added to render the
    image twice as large and scale it smoothly down, which improves images at
    smaller DPI values.
  - An option to keep the text cursor in the current line, when using the
    horizontal arrow keys (off by default) (wish #779)
* Improvements:
  - LilyPond 2.18+ \relative { ... } without start pitch is now supported
  - It is possible to use no start pitch on abs->rel conversion and specify
    the desired behaviour using two checkboxes in the tools->pitch menu.
  - Clicking a point and click link in the Music View now remembers the previous
    position
  - Autocompile was not triggered in some circumstances.
    Now it is also triggered:
    * when a document is saved
    * when undoing a change after a save (i.e. the undo would reset the
      "modifified" flag of the document)
  - When tapping a tempo in the Score Wizard, it is now configurable whether
    a "common" metronome value is picked, or the exact tapped BPM (#792)
  - Allow zooming to 800% in Music View (#800)
  - When closing a document that has an engrave job running, the user is warned
    and can choose whether to wait for the job to complete, to abort it, or to
    cancel the closing.
  - Tabbar and document list show in the document icon whether the last
    engraving was successful (#636)
  - Comment and Uncomment snippets are improved and now in the Snippet menu
  - Score Wizard:
    - add C-Melody Sax (#810)
* Bug fixes:
  - fix #669 make click and drag working again
  - fix #786 'Replace all' only works when run twice
  - fix #793 Command autocompletion doesn’t work in figuremode
  - fix #806 MIDI file not updated in MIDI Player when using "master" variable
  - fix #807 search does not realize that content is changed
  - fix #808 \figuremode should be enclosed within \new FiguredBass
* Translations:
  - updated: Dutch, Italian


## 2.18.2 -- December 26th, 2015

* Requirement changes:
  - Frescobaldi now requires python-ly 0.9.3
* Improvements:
  - More flexible colored HTML export and copy
  - Tabs now show the push-pin icon when a document is always engraved
  - Autocomplete correctly again after '\markup' without opening bracket
  - Enable Ctrl-Enter in Custom Engrave dialog (issue #691)
* Bug fixes:
  - fix AttributeError: 'SourceViewer' object has no attribute '_reply' (issue
    #789)
  - fix TypeError: QPen(): argument 1 has unexpected type QBrush
  - fix some bugs in Quick Insert panel
* Translations:
  - updated: Dutch, French, Italian, Ukrainian


## 2.18.1 -- May 24th, 2015

* New feature:
  - New command line option -V, showing version information of all supporting
    modules such as Python, Poppler, Qt4, etc.
* Improvements:
  - The print dialog remembers the last used printer and options
  - Improved icons for File->Close, Snippets->Repeat last note/chord and
    Snippets->Document Fonts
  - Holding the engrave button also shows Engrave publish and custom actions
  - Tab bar uses scroll buttons on Mac, like the other platforms
  - Automatic engrave only engraves *.ly documents, not *.ily etc
* Bugfixes:
  - Fix document panel is resized when engraving (issue #660)
  - Fix convert-ly adding linefeeds / carriage return on Windows (issue #649)
  - Fix open in running instance when using Python 3 (issue #634)
  - Fix crash when opening non-existing file in running instance (issue #650)
  - Fix icons missing on Windows with system icons enabled (issue #643)
  - Fix Wrong encoding in Score Wizard with Russian locale (issue #641)
  - Fix running LilyPond tools on Mac (pre-built app) (issues #633, #589)
  - Fix ValueError: invalid literal for int() with base 10 (issue #669)
  - Fix UnicodeEncodeError on convert-ly with some languages (issue #674)
* Translations:
  - updated: Dutch, Czech, Ukrainian, Chinese Simplified


## 2.18 -- March 7th, 2015

* Important notes about installing and for packagers/distributors:
  - Frescobaldi is now dependent on the package 'python-ly'. This package
    needs to be installed so that Frescobaldi can run.
    It is listed among the dependencies in the INSTALL file and it can be found
    at https://pypi.python.org/pypi/python-ly.
    Previously, this python package was contained in the frescobaldi_app folder.
    So, when overwriting previous Frescobaldi installations, be sure that any
    remnants from the old 'ly' package are removed, with a command like:
        rm -r /usr/local/<python site-packagesdir>/frescobaldi_app/ly
    Otherwise, Frescobaldi won't find the new ly module and will fail to run.
    Python-ly version 0.9 is required for Frescobaldi 2.18.
  - Python 3.2 (or higher) is supported and recommended! But Python 2.7 will
    continue to be supported during the full Frescobaldi 2 lifecycle.
* New features:
  - Midi import, using the LilyPond-provided midi2ly tool
  - ABC import, using the LilyPond-provided abc2ly tool
  - In the Editor Preferences, you can select which quotes will be used as
    single and double (primary and secondary) typographical quotes (issue #529)
  - The music view now can display a PDF document with two pages next to each
    other, starting with a right or left page, and in single pages (issue #575)
  - A new pitch tool, Mode shift, which can be used to change all or selected
    notes to a specified mode or scale.
  - Commands to convert rests to spaces or vice versa, and to convert pitched
    rests (like c'4\rest) to normal rests, contributed by Peter Bjuhr.
  - Command to open LilyPond data directory (useful if you want to study Lily's
    own init- and Scheme files).
* Improvements:
  - The Insert menu got renamed to Snippets, making more clear how it is used
    and can be changed. When copying text to a new snippet, the snippet is added
    to the menu by default, but the user can change that while editing.
  - Ctrl+Break (LilyPond → Abort Engraving Job) also stops an autocompile job
    if one is running.
  - The SVG View now displays a default gray background when no document is
    loaded, which is more helpful than a white background.
  - When right-clicking in the editor, the editor does not scroll anymore to
    show more surrounding lines.
  - Multi-line block comments are now also foldable (issue #587)
  - The magnifying glass in the Music View does not clip to the page borders
    anymore, which was annoying when showing many pages in a small size.
  - To save space in the toolbar, the almost never used Save As... button was
    removed. But when holding the Save button longer, three choices pop up:
    Save, Save As and Save All.
  - Ctrl-Mousewheel zooming the LilyPond Log now works properly.
* Bugfixes:
  - The german ("deutsch") pitch names asas and heses are now handled correctly.
    Previously, when translating the "nederlands" beses to german, it was output
    as bes, instead of heses. Same for "norsk" and "suomi" (issue #415)
  - If the preference "Open default viewer after successful compile" is enabled,
    the viewer to be opened is determined from the actual results, instead of
    the default output format. This fixes the PDF view opening instead of the
    SVG view, when the SVG format was chosen in the Engrave Custom dialog.
  - fix AttributeError: 'unicode' object has no attribute 'insert' (issue #543)
  - the transpose functions will not transpose the chord after \stringTuning
    anymore (issue #539).
  - fix error when opening a "recent file" that has been deleted (issue #597)
  - Quick Insert articulations etc. now also work with q (repeated) chords
    (issue #628, fixed in python-ly)
  - Quick Insert: do not add articulation to the duration of a \tuplet command
    (issue #631, fixed in python-ly)
* Translations:
  - updated: nl, fr, ru, it


## 2.17.2 -- January 17th, 2015

* Bugfixes:
  - fix AttributeError: 'unicode' object has no attribute 'insert' (issue #543)
* Translations:
  - updated: nl, fr, it


## 2.17.1 -- December 26th, 2014

* Bugfix:
  - on quit, respect cancel (issue #531)


## 2.17 -- December 26th, 2014

* New features:
  - Preference for the number of contextual lines to show at least, when the
    text view is scrolled to a cursor position (e.g. by clicking on a link, or
    when jumping between search results. Wish: issue #488)
  - Session import/export, contributed by Peter Bjuhr
  - A session can have its own list of include paths, that can be used either
    instead of or in addition to the global list of include paths, contributed
    by Peter Bjuhr
  - Relative mode for MIDI input, contributed by Alex Schreiber (pull request
    #521)
* Improvements:
  - When saving a new file for the first time, a default filename is provided,
    based on composer and title of the score (wish: issue #472)
  - Printing the music PDF now honors the duplex settings
  - MusicXML export has improved by using the ly.music module that has a notion
    of the music events and time/duration of those events. Although ly.music is
    authored and maintained by Wilbert Berendsen, the MusicXML export module is
    contributed by Peter Bjuhr
  - workaround a LilyPond buglet in point-and-click highlighting of quoted
    strings: although the textedit uri points to the closing quote, the string
    is correctly highlighted
  - don't disable run button of Engrave Custom dialog for autocompile jobs
  - let autocompile jobs finish before starting a new one (comments issue #120)
  - don't always run autocompile job for the first opened document
  - after a successful compile the default music viewer (pdf or svg) is
    activated. This can be suppressed in the LilyPond prefs (wish: issue #435)
  - the music view does not switch documents anymore when a compile is finished
    but the user is working on a different document (wish: issue #513)
  - tooltips for the panel title and float/close buttons
  - error handling in I/O-related operations has improved
  - Ctrl+C in editor view does not copy HTML, only plain text (issue #517)
  - Features that are in development can be enabled by checking Preferences→
    General→Experimental Features→Enable Experimental Features. Some features
    that are not completely finished are hidden by default but become visible
    when this preference is enabled. New features are enabled after a restart,
    or when a new main window is created using Window→New.
* Bugfixes:
  - fix AttributeError: 'bool' object has no attribute 'endswith' in
    lilypondinfo.py, toolcommand()
  - fix AttributeError: 'NoneType' object has no attribute '_register_cursor'
    (cause in music.py, get_included_document_node())
* Installation:
  - Python 2.7 is now required.
* Translations:
  - updated: nl, pt_BR, fr, it, de
  - new (partial): Chinese Traditional, Simplified and Hong Kong by Anthony Fok


## 2.0.16 -- June 9th, 2014

* Translations:
  - updated: nl, fr, it
* New features
  - preference to automatically strip trailing whitespace on save (issue #274)
  - in Tools -> Rhythm: new command to remove duration scalings that contain
    a fraction value (the action was already available for some time, but it
    wasn't in the menu)
  - new option to copy only the styled HTML contents to the clipboard
    wrapped in a pre tag, not a full HTML document
* Improvements:
  - jumps in the Document Outline also allow navigating back
  - autocompile does only happen when a document has toplevel markup or music
  - LilyPond instance can be selected in convert-ly dialog (wish #311)
  - Score Wizard: In the midi section the \tempo x=y syntax is now used when
    LilyPond version >= 2.16 is used (issue #337)
  - Score Wizard: new brass instruments contributed by Ryan Michael McClure
  - in the builtin manual, if there is no "Next:" page, add a link to the next
    page of the first parent page that has a next page. The link is called
    "Next Chapter:" and allows for continuous reading of the manual.
  - some missing commands and functions were added to highlighting and
    autocompletion
  - the Document Fonts snippet doesn't require setting the staff size anymore
  - View -> Folding -> Fold all now folds all subregions as well, making
    gradual unfolding easier (wish #394)
* Bugfixes:
  - fix sticky document setting lost on reload (issue #409)
  - fix html export and copy not using the correct color scheme
  - fix AttributeError in handle_lyricmode while typing \lyricmode
  - fix LilyPond version chooser not defaulting to the default LilyPond version
  - fix indenter aligning on comment
  - fix AttributeError: QStackedWidget object has no attribute cursorForPosition
    on doubleclick in the text, reported by an Apple user
  - fix AttributeError: 'ScoreWizard' object has no attribute 'showInsertDialog'
    reported by an Apple user
  - fix UnicodeDecodeError in lilypondinfo datadir method


## 2.0.15 -- March 11th, 2014

* Translations:
  - updated: nl, fr
* New features:
  - in context menu: Jump to definition (wish #123)
  - in View menu: view file or definition at cursor, combines the old
    File->Open File at Cursor action with the new Jump to definition action
  - new toolbar buttons to browse back after a jump to definition
* Improvements:
  - better highlighting of figuremode
* Bugfixes:
  - fix ValueError message when typing << >> or \partcombine
  - fix IndexError when typing 'variable ='


## 2.0.14 -- March 7th, 2014

* Translations:
  - updated: nl, fr
* New features:
  - the status bar now shows the position in the music or the length of the
    selected music
  - highlighting and auto-completion for commands that are new or have changed
    syntax in LilyPond 2.18, such as \hide, \omit, \undo, \override, \tweak,
    \accidentalStyle, etc.
  - New editor option to wrap lines in the editor view to avoid horizontal
    scrolling (wish #45)
  - Custom engrave: the anti-alias-factor can be set in the dialog (wish #361)
  - on Mac OS X the applications remains active when all main windows are
    closed. This is expected behaviour on Mac OS X.
  - New builtin snippet, linked to Ctrl+D by default, to double the current
    line or selection (issue #340)
  - A new preference for new documents: whether a new document is created empty,
    with the preferred LilyPond version in it, or using a template from the
    snippets list
  - New menu command: LilyPond->Show available fonts (wish #341)
  - Music View: rendering in small sizes has been improved
* Improvements:
  - In the score wizard it is possible to enter a custom string tuning for the
    plucked string instruments, and the Ukulele is added (issue #342)
  - In the score wizard you can enable Smart neutral stem direction, which adds
    the Melody_engraver to the Voice context, resulting in a logical direction
    for notes on the middle staff line (issue #371)
  - Print source, Copy colored HTML and Export source as colored HTML: add line
    numbers if enabled in the preferences.
  - In the Editor preferences, it is adjustable whether HTML export or copy use
    a stylesheet or inline style attributes.
  - It is now possible to copy syntax-highlighted HTML as plain text to the
    clipboard, by enabling the preference setting.
  - MIDI input: add key signature alterations mapping, by Olivier Samyn
  - New barline types in the Quick Insert panel, the barlines are written
    in the correct style, depending on the LilyPond version set in the document
    (issue #365).
  - In the output-suffix (the scheme output-suffix variable or
    \bookOutputSuffix), non-alphanumeric characters (except '-' and '_') are
    replaced with '_', just like LilyPond itself does it (issue #373).
* Bug fixes:
  - Fixed issue 336: TypeError on MusicXml export
  - Fixed error message when exporting keyboard shortcuts on platforms that do
    not have the HOME environment variable set
  - Fixed IndexError when transposed notes would get unexisting alterations,
    e.g. when a cis is transposed from c to cisis. The note is then altered,
    just like LilyPond handles this.
* Temporarily removed feature:
  - MusicXML export has been temporarily removed from the File->Export menu.
    It is still visible in the git checkout. It is also available in the ly
    command (in the python-ly package, and also in Frescobaldi's git checkout)
    but it needs more testing and robustness before it is usable in Frescobaldi.


## 2.0.13 -- December 31st, 2013

* Translations:
  - updated: nl, fr
* New features:
  - A new option LilyPond->Auto-engrave, that runs the engraver in preview mode
    every time the document changes
  - An option to hide log display for automatically started engraving jobs
  - Real-time Midi capturing, contributed by Manuel Mchalwat (this was actually
    in 2.0.12, I just forgot to write it in the ChangeLog!)
  - Basic MusicXML export, contributed by Peter Bjuhr (this was also already
    added in Frescobaldi 2.0.12)
  - The "master" variable is back, allbeit in a slightly different
    implementation: the redirected filename is not directly given to a LilyPond
    process running on behalf of the current document, but the other document
    is loaded (if it wasn't already) and LilyPond is run on that document.
* Bug fixes:
  - Fix UnboundLocalError in ly.docinfo e.g. when showing the Tools->Pitch->
    Language menu
  - Fix issue 332: Cursor didn't move on undo/redo
  - Fix issue 315: chords: \include "predefined-guitar-fretboards.ly"
    (the file was added, but the include files weren't written in the document)


## 2.0.12 -- December 26th, 2013

* Translations:
  - updated: cs, nl, fr, es
* New features:
  - Edit->Select Block has finally been implemented
  - A viewer for LilyPond-generated SVG files has been added by Peter Bjuhr.
    This viewer (accessible via Tools->SVG Viewer) currently has one-way point
    and click. This only works with recent development versions of LilyPond,
    that add the point and click information to SVG files. In the future, the
    SVG view may become a fully fledged graphical music editor.
  - The default output format can be set in the LilyPond preferences (the
    current options are PDF or SVG, the default is PDF)
* Improvements:
  - The indenter's handling of tabs and spaces has been improved. A tab always
    starts a new indent level, and aligning is now always done with spaces.
    The default is still using 2 spaces for indent, but it is now configurable
    in a new settings panel Editor Preferences.
  - Besides the good old Preview and Publish modes a new mode has been added:
    Layout Control. This mode uses the settings on the preview mode panel, which
    has been renamed to Layout Control Options. The layout of the panel has been
    improved. The Preview mode is reverted back to enabling only point and click
    links. In the Engrave (custom) dialog the run mode can be chosen and the
    commandline edited directly.
  - Entering staccatissimo writes -! when the document specifies a LilyPond
    version >= 2.17.25, otherwise -|
  - When editing keyboard shortcuts, conflicts are directly shown as they are
    entered; better support French keyboards (contributed by Nicolas Malarmey)
  - Better Mac OS X icons (contributed by Davide Liessi)
  - The internal handling of manipulations like transpose, translate, and the
    various rhythm commands has become less dependent on Frescobaldi code.
    These functionality now resides in the ly module and could be used by
    other applications. The commands now can work on any ly.document, which
    need not be a Frescobaldi document.
  - The internal help system has seen a massive overhaul: help files are now
    very easy to write in a simplified markdown-like syntax. Adding help pages
    is very easy by dropping a *.md file in the userguide/ directory. Every
    paragraph in a help file is automatically added to the POT file and can be
    translated by editing the language's PO file.
* Bug fixes:
  - Music View: horizontal scrolling using trackpad now works with kinetic mode
    enabled. Fixes #248.
* Removed feature:
  - The 'master' variable is no longer supported, it's goal has been superseded
    by the 'Always Engrave' option, which is also saved in the session. This
    decision was taken to simplify the handling of files created on behalf of
    a document.


## 2.0.11 -- October 16th, 2013

* Translations:
  - updated: cs, nl, fr, es
* New features:
  - New preview mode tool, enabling different modes to debug layout issues,
    contributed by Urs Liska and some other LilyPond developers
  - Frescobaldi now has a manpage, kindly provided by Ryan Kavanagh
  - Import MusicXML (using musicxml2ly), contributed by Peter Bjuhr
  - New Quick Insert buttons for different kinds of grace notes, contributed
    by Peter Bjuhr
  - Import and export of keyboard shortcuts and font & color schemes,
    contributed by Nicolas Malarmey.
  - New Modal Transpose action, contributed by Christopher Bryan
  - New actions to remove articulations etc. from music (wish #180)
  - Edit->Copy to Snippet, to copy the selection or the full document
    contents to a new snippet
* Improvements:
  - highlighting and auto-completion of Scheme code has been improved
    by Nicolas Malarmey.
  - when switching documents with multiple editor views open, and one of the
    views displays the document, that view is made current, instead of changing
    the document in the current view.
  - the tempo-tapping button in the score wizard now uses the average clicking
    speed instead of computing the bpm at each click (implementing wish #169)
  - under the File menu there is also a New with Wizard... action calling the
    score wizard, creating a new document when clicking Ok, contributed by Urs
    Liska
  - Word-related cursor movements have been improved. The backslash is now
    considered a word boundary, even if there are no spaces between several
    backslashed commands. Fixes wish #106.
* Bug fixes:
  - various fixes and improvements on Mac OS X by Davide Liessi
  - fix splash screen shown as grey rectangle on some systems
  - in the LilyPond log, clicking on error mesages in files with '..' in their
    path (happens when using e.g. \include "../blabla.ly") now works.


## 2.0.10 -- May 12th, 2013

* Translations:
  - updated: nl, de, fr, cs, es, it
* New features:
  - Document Outline tool with tooltips showing portions of the document.
    The patterns that are used for the outline can be modified by the user.
* Improvements:
  - Highlight more music functions that were added in LilyPond 2.16
  - Better chord mode highlighting
* Bug fixes:
  - fix QPyNullVariant error message on Mac OS X when setting helper app prefs
  - fix Scorewizard error in Leadsheet with accompaniment and ambitus turned on
  - fix #113: add files opened via file manager to recent files
  - fix #143: don't count tremolo repeat as a duration


## 2.0.9 -- March 23rd, 2013

* Translations:
  - updated: nl, de, uk
* New features:
  - Frescobaldi now detects when other applications modify or delete open files
    and displays the changes in a dialog, where the user can reload or save the
    affected documents. The file-watching is turned on by default, but can be
    disabled. (wish: issue #103)
  - File->Reload and Reload All: reload the current document or all documents
    from disk. This action can be undone with Ctrl-Z.
  - Frescobaldi now can be configured to open the generated PDF files when
    opening a LilyPond document, even if they are not up-to-date. It then shows
    a red background in the document chooser. See Preferences->Tools->Music View
  - Music->Reload: switches the Music View to the current source document and
    re-checks for updated PDF documents. If there are no updated PDFs it even
    tries to load non up-to-date PDFs (regardless of the setting above)
  - New --list-sessions commandline option to list the named sessions
  - New actions View->Matching Pair and Select Matching Pair to jump to or
    select the range of matching parentheses, braces etc (wish: issue #105)
  - Quick Insert: \melisma, \melismaEnd spanner button (idea: issue #88)
* Improvements:
  - Custom defined markup commands are also auto-completed
  - Better default font on Windows
  - Action "Always Engrave this document" also available in document context
    menu (in documents list and in tabbar)
  - Don't check included files multiple times for defined commands etc.
  - Highlighting matching characters, such as slur, brace, << >>, etc does not
    take a long time anymore when editing or moving through a long document
  - string numbers are highlighted (and understood) correctly outside chords
    (LilyPond 2.16 syntax change)
  - Export colored HTML now uses CSS classes, makes it easy to change the high-
    lighting in the HTML later (idea: issue #89)
* Bug fixes:
  - Fix hyphenation of words with accents (reported by Andreas Edlund)
  - Fix Save As... on Mac OS X (issue #104)
  - Fix startup failure on Mac OS X (issue #77)
  - Fix QPyNullVariant error messages with some PyQt versions
  - Workaround two PyQt bugs:
    * fix score wizard AttributeError message when using sip-4.14.3/PyQt-4.9.6
    * fix large delays in editor when using sip-4.14.3/PyQt-4.9.6 (issue #100)
  - music highlighting of a note after \unset someVariable is now correct
  - fix Python error message when a document (marked as Always engraved) is
    engraved which didn't have yet the PDF displayed


## 2.0.8 -- September 14th, 2012

* Translations:
  - updated: ru, cs
* New features:
  - File->Open file at cursor (wish #84)
* Improvements:
  - always normalize paths in point&click links, so files included via
    constructs like \include "../songs/song1.ly" are found
* Bugfixes:
  - fix behaviour of 'output' variable


## 2.0.7 -- August 16th, 2012

* Translations:
  - updated: nl, cs, it, fr, es
* New features:
  - command to show music view maximized, useful on small screens
  - kinetic scrolling in the music view, making the movements easier on the
    eyes, contributed by Richard Cognot
  - music view scrollbars can be hidden via preferences->tools->music view
* Improvements:
  - status of "Always Engrave" is saved in session (wish #76)
  - the 'View' -> 'Music View' submenu is now a top-level menu 'Music'
* Bugfixes:
  - fix "NameError: global name 'X_OK' is not defined" when a helper application
    has an absolute path
  - fix python exception when helper app does not exist, now a regular message
    is shown


## 2.0.6 -- April 30th, 2012

* Translations:
  - New Ukrainian translation by Dmytro O. Redchuk
  - updated: nl
* Bugfixes:
  - fix cut-assign
  - fix startup failure on Windows when 'open in running app' is enabled and
    the user's username has non-ascii characters (issue #53)
  - fix TypeError on opening LilyPond documentation in some cases on Mac OS X


## 2.0.5 -- April 25th, 2012

* Translations:
  - updated: fr, nl, es
* New features:
  - Regions of text can be collapsed/expanded (View->Folding->Enable Folding)
  - Files can be opened in running instance, if enabled in settings
  - New document variable: 'output' which can be set to the basename, folder, or
    list of names or folders to look for output documents. Overrides the default
    behaviour of parsing the document for all the included files and LilyPond
    commands that specify the output file name.
  - New snippet action to recover changed or deleted built-in snippets
  - New snippet action to configure keyboard shortcut without opening editor
  - Alt+Up and Alt+Down jump between blank lines (implemented as snippets),
    with Shift they select text
  - New command in View->Music View and Music View contextmenu: "Original Size"
  - Optionally scroll Music View while highlighting objects text cursor is at
  - In-place editing by Shift-clicking a note or right-click->Edit in Place
* Improvements:
  - Copied images from Music View carry correct DPI information
  - Autocomplete also looks for variable definitions in \include files
  - Running convert-ly (or undoing it) does not erase point and click positions
    anymore
  - Saving a template now shows existing template names in a popup and warns
    when (but allows) overwriting an existing template
  - Much better default background color for the Music View
  - When dragging the time slider in a MIDI file, program and controller changes
    are followed (issue #26)
  - On Windows, better try to find LilyPond even if it is not in the PATH
  - Snippet editor warns when closing modified snippet
  - Accelerators (the underlined characters) in menus such as Recent Files,
    Session and Insert that are are automatically created, are determined in
    a smarter way
* Bugfixes:
  - fix Ctrl+K deleting a line too much in some cases
  - fix RuntimeError on Ctrl+N, Ctrl+F, Ctrl+W
  - fix TypeError on running convert-ly with English messages on Windows
* For Linux distribution packagers:
  - The CC-licensed zoom-{in,out} icons are now replaced with GPLled ones


## 2.0.4 -- March 7th, 2012

* Translations:
  - updated: pl, nl, cs
* New features:
  - view->line numbers
  - in the documents list, it is now possible to right-click a group of selected
    documents (or a directory name, if grouping is enabled), to close or save
    multiple documents at once.
  - automatic completion in the snippet editor
  - python snippets may now define a main() function that can do everything
  - new delete-lines snippet, bound by default to Ctrl-K
  - splash screen on startup (can be turned off in the preferences)
* Improvements:
  - opening many documents (e.g. a large session) is now much faster
  - waiting for LilyPond to return information on Settings->Ok now does not
    block the user interface anymore and shows progress if it takes some time
  - built-in manual now documents settings and session dialog
* Bug fixes:
  - fix icon theme index files not in source tarball (regression since 2.0.3)
  - fix hyphenation dictionaries not in source tarball
  - fixed memory leak (closed documents that had been shown remained in memory)


## 2.0.3 -- February 17th, 2012

* Translations:
  - New translation: Brazillian, by Édio Mazera, thanks!
  - updated translations: es, fr, it, nl
* New features:
  - pager in musicview toolbar
  - tools->open command prompt to open a terminal window
* Improvements:
  - improved "Comment" snippet; add "Uncomment"
  - Home and Shift+Home now move the cursor to the first non-space character
  - Shift+Return now does not enter a line separator anymore, which could
    cause wrong point and click locations
  - blinking rectangle highlights new cursor position on point and click
* Bug fixes:
  - fix zooming Music View out while on last page (issue #32)
  - changing keyboard shortcuts in preferences now works on Mac OS X
  - fix { } or << >> inside lyricmode
  - in doc browser, don't display bogus versions when network is inaccessible
* For Linux distribution packagers:
  - the bundled Tango icon set is now used as an icon theme, which makes it
    possible for distribution packagers to remove the icons/Tango directory and
    instead make Frescobaldi depend on the tango-icon-theme package.


## 2.0.2 -- January 16th, 2012

* New features:
  - optionally run LilyPond with English (untranslated) messages
  - print button in help browser and documentation browser
* Improvements:
  - "Manage templates" command added in File->templates menu
  - more snippets in Insert menu
  - context menu on snippet list
  - enlarged some too small icons
  - added some more hyphenation dictionaries
  - file entry fields (like in preferences) are faster
  - on non-X11 platforms the maximized state of the window is remembered
* Bug fixes:
  - make terminating LilyPond work under Windows
  - make convert-ly work under Windows
  - snippet import/export now works in the Windows-installer binary
  - PDF now correctly updates when "Save document on compile" is enabled


## 2.0.1 -- January 8th, 2012

* Updated translations: cs, de
* Bug fixes:
  - fix accented letters in filenames on Windows
* Improvements:
  - some hyphenation dictionaries are now bundled
  - font preference for documentation browser
  - new self-contained installer for MS Windows


## 2.0.0 -- December 26th, 2011

* Updated translations: fr, nl, es, it, cs
* Bug fixes:
  - when changing LilyPond instance that was default, keep it as default
* New features:
  - new dialog and snippet to set the fonts for a LilyPond document
  - the tabs can be hidden and shown via the mainwindow context menu
  - autocomplete on #'font-name, with font preview
* Improvements:
  - Shift-F1 (What's This) now works in dialogs
  - the tab bar can be hidden via the main window context menu


## 1.9.5 -- December 20th, 2011

* Updated translations: es, nl, cs
* Bug fixes:
  - charmap now avoids characters "narrow" builds of Python can't handle
  - fix incorrect midi tempo when midi file contains tempo changes
  - fix importing the pyportmidi._pyportmidi module if that is used
  - really honor 'delete intermediate files' option
* New features:
  - Documents list with optional per-directory grouping
  - helper applications can be specified to override operating system defaults
  - list of generated files in LilyPond menu
* Improvements:
  - tooltips in music view show variable name of music definition
  - search bar in documentation browser
  - autocomplete on \include, \language
  - other small cosmetic improvements


## 1.9.4 -- December 5th, 2011

* Updated translations: es, fr, nl
* New features:
  - Engrave custom dialog for specifying other engraving formats and options
  - Character selection tool to insert characters from all unicode blocks
* Bugfixes:
  - fix crash on 64bit Linux and Windows introduced in 1.9.3


## 1.9.3 -- December 1st, 2011

* LilyPond Documentation browser:
  - multiple versions of LilyPond documentation can be browsed, local and remote
* Bug fixes:
  - fix missing result files for documents with square brackets in filename
  - fix error message when running LilyPond on modified document with a name but
    which was never saved before (happens e.g. when opening a non-existing file)
  - fix crash when MIDI synth stopped or disconnected while playing (issue #4)
  - fix using PortMidi via ctypes under 64bit Linux (issue #3)
  - fix error message on invalid textedit links
  - fix scrollbars covering search box in some GUI styles (issue #2)
* Improvements:
  - lyrics hyphenation doesn't require text to be selected anymore
  - don't try to load non-existing file when clicking a point-and click link
  - cursor now remains in same column while moving vertically after indent
  - add articulations etc to autocompletion
  - don't show the log if the user aborted a job


## 1.9.2 -- November 11th, 2011

* Translation updates: es, nl
* New features:
  - Built-in MIDI player
  - Snippets can also be put in File->New from Template. When triggered via that
    menu, a new document is created. There's also a command to save the current
    document as a template.
  - Import and export of snippets.


## 1.9.1 -- October 11th, 2011

* Translation updates
* Help in much more dialogs
* New icons for some commands
* It is now possible to set the preferred Qt GUI style
* Always makes backup copy on save, config setting to retain it
* Detailed version info in about dialog
* Lots of small improvements, such as:
  - Apply Rhythm dialog remembering rhythms
  - snippet error messagebox now has Edit Snippet button
* New commands:
  - Cut and Assign
  - Copy to Image
  - Tools -> Format to format whitespace
  - Update with Convert-Ly (with diff view)
* Bugfixes:
  - fix error message on View->Clear error marks
  - fix autocomplete picking second item if no item is highlighted
  - some Parser (highlighting) fixes
  - color buttons now show color on all platforms
  - fix error message on saving settings if no LilyPond was installed


## 1.9.0 -- September 27th, 2011

* Full rewrite, not depending on KDE4 libraries any more
* Much more modular internal design, easier to add features
* All translations imported


## 1.2.1 --

* Fixes:
  - Correct spacing alist names in LilyPond 2.14 in blank paper tool
  - Fixed misinterpreting crescenco (\<) as a chord by articulations quick panel
* Translations:
  - Galician updated by Manuel A. Vázquez
  - Italian updated by Gianluca D'Orazio


## 1.2.0 -- December 26th, 2010

* Translations:
  - Dutch updated by Wilbert Berendsen
  - Turkish updated by Server Acim
  - French updated by Valentin Villenave and Ryan Kavanagh
  - Czech updated by Pavel Fric
  - Spanish updated by Francisco Vila
  - German updated by Georg Hennig
  - Polish updated by Piotr Komorowski


## 1.1.8 -- November 9th, 2010

* All pitch name related functions (detection and translation) support
  the new \language LilyPond command (as of LilyPond 2.13.38).
* Installation: An option has been added to suppress checking presence and
  versions of required python modules.
* Translations:
  - Dutch updated by Wilbert Berendsen
  - Turkish updated by Server Acim
  - Czech updated by Pavel Fric
  - German updated by Georg Hennig
  - French updated by Valentin Villenave


## 1.1.7 -- October 4th, 2010

* New features:
  - New tool to download LilyPond binary releases. Go to Settings -> Configure
    Frescobaldi -> LilyPond Preferences, Versions -> Add -> Download to use it.
  - New rhythm command "Make implicit (per line)" that removes repeated
    durations, except for the first duration in a line.
* Quick Insert Panel:
  - New default shortcuts for Slur: Ctrl+( and Breathing sign: Alt+'
* Bugfixes and improvements:
  - Don't error out if certain GUI containers can't be found, due to missing
    objects in the local frescobaldiui.rc file. Display a message instead.
* PDF Preview:
  - If 'Sync preview' is unchecked, the preview now also doesn't open newly
    created or updated PDF documents. As a result, the 'Disable PDF preview'
    setting became superfluous and has been removed.
* LilyPond Log:
  - The toolbar at the bottom has been removed, as all functions in the main
    menu and toolbar are now equivalent.
* Translations:
  - Dutch updated by Wilbert Berendsen
  - Turkish updated by Server Acim


## 1.1.6 -- September 10th, 2010

* New features:
  - New built-in MIDI player using the KMidPart of KMid 2.4.0 or higher
  - Notification popup when a long build finishes while Frescobaldi is hidden
  - Quick Insert: new panels for dynamics, bar lines, spanners, arpeggios, etc
  - LilyPond version to use configurable per session
* Bugfixes and improvements:
  - Fix error message on Cut&Assign, introduced in 1.1.3
  - Expand dialog: Don't insert expansion when closed with ESC
  - Handle keyboard interrupt (SIGINT) nicely, don't show the bug dialog
  - Fix session --start commandline option
  - Blank staff paper: improved bar line distances with recent LilyPond versions
* Installation:
  - Install Frescobaldi icon as SVG, not SVGZ
  - make uninstall now possible


## 1.1.5 -- August 16th, 2010

* Bugfixes and improvements:
  - Work-around a crash introduced in KDE 4.5 when using the --smart option
    to set the cursor position.
  - Fix Python error message when adding a new LilyPond version with the "Set as
    default" option checked.
* Translations:
  - Czech updated by Pavel Fric
  - Polish updated by Piotr Komorowski
  - French updated by Ryan Kavanagh
  - Turkish updated by Server Acim


## 1.1.4 -- July 28th, 2010

* Bugfixes:
  - Fix Point and Click when running from 'run' script


## 1.1.3 -- July 25th, 2010

* General:
  - Tabs can be reordered (can be turned off)
  - Tabs don't get automatic shortcuts, they sometimes conflict with ours
  - the right tool dock has been made slightly larger by default
* New: Session Management, in two ways:
  - Basic session management: if you log out with Frescobaldi running and then
    back in, Frescobaldi will reopen the documents that were open at logout.
  - Advanced named session support. A session defines a list of open documents,
    and optionally a base directory. More features will be added later to be
    able to use this as a light-weight project tool.
* Context sensitive LilyPond help:
  - added support for internals reference: contexts, grobs and engravers
* Bugfixes:
  - Fix crash when editing toolbars
* Installation:
  - A 'run' script has been added to run Frescobaldi from the tarball (or even
    SVN) without installing.
  - Using CMake out-of-source is now easier: icons and translations are not
    rebuilt anymore so the Frescobaldi install procedure does not need LilyPond
    and 'convert' (from ImageMagick) anymore. The icons and translations are in
    the prebuilt/ directory. Simply removing this directory restores the old
    behaviour (useful when you want to develop Frescobaldi from a release
    tarball, although a fresh SVN checkout is recommended in that case).
* Translations:
  - Dutch updated by Wilbert Berendsen
  - Turkish updated by Server Acim


## 1.1.2 -- July 8th, 2010

* New features:
  - Segno bar line added (available in LilyPond 2.13.19 and higher)
  - It is now possible to configure the path that is used to find
    files that are included via the LilyPond \include command.
  - New 'Close other' action to close all documents except the current
  - Print and View icons in the toolbar to print music and open PDF and MIDI
    files in their external helper applications
* Printing:
  - Printing generated PDF files now uses a print dialog, instead of just
    sending the PDF to the 'lpr' command.
* Run LilyPond:
  - warn if the document contains a conflicting point and click setting
* General:
  - print and email actions have moved to the File menu
  - close button on document tabs (can be turned off in Settings->Editor Comp.)
  - warnings and notifications have a "don't ask again" checkbox, and can be
    turned back on in the settings
  - progress indicator saves the build time in document metainfo
* Autocompletion:
  - only popup completions from the expansion manager on blank lines
* Settings dialog:
  - the settings have been organized in more logical groups
* Installation:
  - building the icons from SVN or out-of-source requires LilyPond >= 2.13.19
* Translations:
  - Dutch updated by Wilbert Berendsen
  - French updated by Valentin Villenave
  - Italian updated by Gianluca D'Orazio


## 1.1.1 -- May 3rd, 2010

* LilyPond Documentation Browser:
  - Indexing help items fixed with new website (2.13+)
* Fixed Python error message on opening settings dialog with recent SIP/PyQt
* Translations:
  - Dutch updated by Wilbert Berendsen
  - Turkish updated by Server Acim


## 1.1.0 -- March 26th, 2010

* It is now possible to use multiple versions of LilyPond easily from within
  Frescobaldi. LilyPond instances can be configured under Settings, Paths.
  There is also a custom Run LilyPond command where a version can be chosen,
  among other options.  And Frescobaldi can be configured to automatically
  choose a LilyPond version according to the document's \version statement.
* Score Wizard, Choir:
  - New lyric option "Distribute stanzas" to spread the stanzas between staves.
    This option only has effect when there are three or more staves, and is very
    useful if there is a large number of stanzas that apply to all voices.
  - Lyric placement is fine-tuned when LilyPond >= 2.13.4 is used, using the
    staff-affinity setting, so lyrics are placed close to the staff they belong
    to. If lyrics apply to multiple voices, the are centered between staves.
    This improves the layout of vocal music if the systems are vertically
    streched by LilyPond to fill the page nicely.
  - New checkbox to create rehearsal MIDI files. If checked, one MIDI file is
    generated for each voice, with the voice standing out in a clear sound and
    the other voices in a lower volume. Repeats are unfolded and lyrics for the
    current voice are also added to the MIDI file.
* Score Wizard, Score settings:
  - New checkbox option to wrap the score in a \book block.
* New dialog to insert special characters from the Unicode table, with the
  ability to assign keyboard shortcuts to often used characters.
* New command: Copy Lyrics with hyphenation removed
* Expansion Dialog:
  - has now some documented default keyboard shortcuts
* Quick Insert Panel:
  - New buttons for \halfopen and \snappizzicato
  - It is now possible to assign keyboard shortcuts to the articulation buttons
* Repeat last expression: don't append space
* Email files: select files with checkboxes instead of Ctrl+Click
* Installation:
  - byte compiling the Python modules can be suppressed by adding
    -DBYTECOMPILE=NO to the cmake command line
  - building the icons from SVN or out-of-source requires LilyPond 2.13.11+
* Some workarounds for subtle SIP 4.10/KDE 4.4 garbage collection bugs


## 1.0.2 -- February 18th, 2010

* Make Frescobaldi working with SIP 4.10 and KDE 4.4


## 1.0.1 -- January 17th, 2010

* Translations:
  - New Galician translation by Manuel A. Vázquez
* Bugfixes:
  - Rumor: Make config dialog more robust if no MIDI outputs available
  - Score Wizard: Fix disappearing instrumentName if this is a markup object and
    the same one as shortInstrumentName
  - Stability improvements
  - Some corrections in the default expansions of the Expansion Manager


## 1.0.0 -- December 26th, 2009

* Editor:
  - Right-click menu action on \include command now opens the named file from
    the LilyPond data directory if that exists and there is no local file with
    that name.
* Repeat last expression (Ctrl+;):
  - Doesn't repeat normal rests and skips, but rather the chord preceding it
  - Keeps the \rest when repeating a pitched rest (e.g. c\rest)
  - Only removes the octave from the repeated pitch (or from the first pitch
    of the repeated chord) inside \relative music expressions
* Blank staff paper tool:
  - option to remove small "FRESCOBALDI.ORG" tagline at bottom
* Score Wizard:
  - Fix lyrics not added if there is only one staff (reported by M. Moles)
* Quick Insert Panel:
  - If cursor is inside a chord, note or rest, the cursor is positioned right
    after the chord, note or rest before the articulation is inserted (if there
    is no selection, in which case the articulation is inserted after all
    chords, notes or rests). So now you can click a note in the PDF and directly
    click a button to add an articulation or ornament etc. without repositioning
    the cursor manually.
* PDF preview:
  - Action in contextmenu to reload PDF document
* General:
  - Fix crash on moving tools around
  - Fix crash on exit on some systems with multiple updated documents open
  - Work around crash on logging out from the built-in terminal and then hiding
    and re-showing it, that occurs due to a bug in SIP 4.9.1
  - ESC key now closes PDF-preview dialogs properly
  - ESC key does not take focus away from editor window if PDF visible
  - Main window is activated when clicking on notes in detached PDF viewer
  - Fix interaction with SIP 4.9.3 (some settings were not saved, like paths)
  - Fix order of cautionary accidentals and octave marks in pitches (affects
    transpose and relative/absolute conversion functions)
  - Fix attribute error on file dialogs in KDE 4.1 (but KDE 4.2 is recommended)
  - Fix document name not shown in tab bar if opening non-existing file
  - Improved hyphenation dictionaries search, also some explanation in docs
* Installation:
  - CMake now does not require a compiler to be present anymore
* Translations:
  - Dutch updated by Wilbert Berendsen
  - Spanish updated by Francisco Vila
  - Turkish updated by S. Acim
  - Italian updated by Gianluca D'Orazio
  - French updated by Ryan Kavanagh
  - Czech updated by Pavel Fric
  - Polish updated by Piotr Komorowski
  - German updated by Georg Hennig


## 0.7.17 -- November 29th, 2009

* Expansion Dialog:
  - It is now possible to assign keyboard shortcuts to snippets in the dialog
  - Improved syntax coloring in snippet entry
* Autocompletion:
  - If the autocompleter does not find any suitable completions, matching
    expansions from the Expansion dialog are shown
* Score Wizard:
  - Harp, Guitar and Jazz Guitar: allow multiple voices per staff
  - Choir: checkbox for automatic piano reduction
* General bugfixes and improvements:
  - When quitting, the last seen documents, starting with the current, are
    closed first. This way, if the user cancels the quit, the current document
    (if modified) remains the same.
  - Files can be opened by dropping them on the Frescobaldi window
  - Fix crash when swichting to a document opened using the Open File dialog
    when multiple files were opened at the same time
  - All pitch manipulation functions better detect the end of unbracketed markup
    expressions like: g g g-\markup \sharp g g g.  Frescobaldi now knows the
    number of arguments each markup command has and will not mistake the g after
    \sharp for a markup argument.
* Installation:
  - building and installing the User Guide has been improved. If meinproc4 or
    the XSL stylesheets can't be found, only a warning is printed and the cache
    file (index.cache.bz2) is not pre-generated, but the install will continue.
    (If there is no cache file, KHelpcenter will generate one on a per-user
    basis as soon as the User Guide is displayed for the first time.)
* Translations:
  - Dutch updated by me
  - Spanish updated by Francisco Vila
  - Polish updated by Piotr Komorowski
  - Czech updated by Pavel Fric
  - French updated by Ryan Kavanagh


## 0.7.16 -- November 15th, 2009

* New command to transpose music
* New commands for conversion between relative and absolute pitches
* New: Alt+Shift+Up/Down selects text till next or previous blank line, and
  Ctrl+Alt+Shift+Up/Down moves the selected block to the next or previous blank
  line. This gives a very quick way to reorder fragments of LilyPond input.
* A new tool to create empty staff paper
* Improved support for quarter tones in all pitch-related functions
* Translations:
  - French updated by Ryan Kavanagh
  - Spanish updated by Francisco Vila


## 0.7.15 -- October 13th, 2009

* New LilyPond documentation browser providing context-sensitive help
* New shortcuts:
  - Repeat selected music, Ctrl+Shift+R: wraps the selection in a
    \repeat volta 2 { music... } construct
  - Insert pair of braces, Ctrl+{: wraps the selection in braces, or inserts
    { newline newline } and places the cursor on the middle indented line.
* New bar lines submenu to insert different types of bar lines
* Expansion Manager:
  - Two cursormarks (|) can be used to select a range of text after expanding
  - New contextmenu command to add selected text to expansions
* Autocompletion:
  - named colors are shown in the right color
  - some often used block commands like \header now also insert the braces,
    and place the cursor between them.
  - names of variables (like composer in the header) automagically append ' = '
    if the remainder of the line does not start with the '=' character.
* New commands in the Log context menu to copy or save its contents.
* LilyPond symbol icons are displayed white if the users color palette settings
  have light text on a dark background. The icons are automatically recolored
  if the user changes the color preferences while Frescobaldi is running.
* The Save As... dialog now really opens in the default directory if the
  document has no filename yet.
* Tools can be shown/hidden with configurable keyboard shortcuts
* Score Wizard: parts can be reordered by dragging with the mouse
* Documentation updates
* Translations:
  - Turkish updated by S. Acim
  - Russian updated by Artem Zolochevskiy
  - Polish updated by Piotr Komorowski
  - Dutch updated by Wilbert Berendsen


## 0.7.14 -- September 12th, 2009

* Log shows elapsed time after successful LilyPond run
* Option to run LilyPond with --verbose output
* Fix Rumor input when key signature is set to anything else than "Auto"
* Misc other bugfixes
* Translations:
  - Czech updated by Pavel Fric
  - Italian updated by Gianluca D'Orazio


## 0.7.13 -- August 9th, 2009

* Make Frescobaldi working again in KDE 4.3 due to changes in KDE and PyQt-4.5
* Translations:
  - Turkish updated by S. Acim
  - Russian updated by S. Poltavski


## 0.7.12 -- July 1st, 2009

* It is now possible to run LilyPond on remote documents and documents that have
  not been saved yet. In such cases Frescobaldi internally saves the LilyPond
  file to a local temporary directory. Point and click also works on remote or
  unnamed documents. This makes it easy to paste something from an email and run
  LilyPond immediately, without bothering to save it first under a suitable file
  name. The local cache is deleted when the document is closed or saved to a
  directory on the local file system.
* It is now possible to configure external applications for PDF and MIDI files.
  These will then be used instead of the KDE default configured applications.
* New align action (LilyPond->Source Document->Indent) that properly indents a
  document or selection of lines. This indenter is a bit more robust than the
  one built into KatePart. The Score Wizard and Expand Manager now also use the
  users indentation settings, instead of always using two spaces indent.
* New shortcuts to insert nice typographical quotes: Ctrl+' for single and
  Ctrl+" for double quotes. Left and right quotes are automatically determined.
  If text is selected, the selected text is put between quotes.
* Repeat last note/chord: only keep articulations and ties.
* Bug fixes:
  - Smart Point and Click remains working if pitches are translated
  - Text editor keeps keyboard focus again when clicked in PDF preview
  - Rumor plugin more stable in keyboard mode and stops cleanly if running on
    Frescobaldi exit
* Translations:
  - French updated by David Bouriaud (thanks!)
  - Dutch updated by self


## 0.7.11 -- June 15th, 2009

* Stability improvements


## 0.7.10 -- June 9th, 2009

* Point and click: Shift-click in the PDF preview now selects music from current
  cursor position to new cursor position. So you can select a music fragment by
  clicking on the first note and then shift-clicking on the last note.
* Editor:
  - Context sensitive context (right-click) menu with, besides the usual cut,
    copy and paste, commands to open \include file, hyphenate lyrics and
    Cut & Assign text (if selected)
  - The Cut & Assign command (Ctrl+Shift+C) now obeys inputmodes. If you e.g.
    cut out some lyrics, the fragment will automatically be wrapped in a
    \lyricmode { } block.
  - Autocompletion for accidental styles
* User Interface:
  - new document tab bar for easy navigation between open files, can be hidden
  - when running LilyPond and the option 'Save document when LilyPond is run' is
    enabled, the Save As dialog is displayed when the document has no filename
    yet.
* Translations:
  - German translation updated by Georg Hennig (thanks!)


## 0.7.9 -- May 23rd, 2009

* Bugfixes:
  - spurious crashes seem to have been gone (by using thread locks on
    katepart's SmartInterface)
* Editing:
  - Alt-Up and Alt-Down now jump to the first line of a blank block instead of
    just the next or previous blank line.
* Quick Insert Panel:
  - ornaments use the default window text color
* Repeat last expression:
  - remove octave mark from first pitch
  - remove barcheck pipe symbols
* Score Wizard:
  - Small fixes to fretted instruments
  - Predefined Guitar Fret option for Chord Names (also in Lead Sheet)


## 0.7.8 -- March 20th, 2009

* New Polish translation by Piotr Komorowski, many thanks!
* Updated translations: tr
* Smart Point & Click: URLs point to correct position even if the document is
  changed without re-running LilyPond. Also the clickable messages in the log.
  Smart Point & Click from the PDF preview only works in KDE 4.2.
* New option to only show the log if LilyPond outputs warnings or errors
* Progress bar in statusbar shows LilyPond progress
* Bugfixes:
  * Make Frescobaldi exit gracefully if a LilyPond job was still running
  * Make Point & Click work again in KDE 4.2 if there are tabs in the document.
  * Fixed Change Pitch Language, sometimes this function didn't work if there
    were complicated markups in the document.
  * Memory usage improvements (some unused objects were not garbage collected)


## 0.7.7 -- March 3rd, 2009

* New comprehensive User Guide in the help menu (F1 key)
* Context sensitive Help buttons in most dialogs
* New Czech translation by Pavel Fric, many thanks!
* Updated translations: ru, nl
* Settings: it is now possible to choose which LilyPond version number to
  use by default for new documents: the version of the installed LilyPond,
  the version of the last conversion rule of convert-ly, or a custom version.
* PDF preview: context menu has a new action to configure Okular
* Score Wizard: if there is more than one part, make separate assignments for
  the parts. This simplifies the generated \score { } section and makes it
  easier to create additional score sections for printing separate parts.
* Bugfixes:
  * Apply/paste rhythm: don't lose parts of text and don't hang if no rhythm
  * Find translations when installed to non-standard directory
  * Avoid double entries in score wizard instrument name language combobox


## 0.7.6 -- February 21st, 2009

* New context sensitive autocompletion feature, supporting:
  * general lilypond commands and markup commands (inside markup)
  * contexts and layout objects and their properties
  * engravers, musicglyph names and midi instrument names
  * most used variable names in \header, \paper, \layout, etc.
  * some often used scheme function names


## 0.7.5 -- February 12th, 2009

* Translations updated: fr, it, nl
* Frescobaldi now can be installed to non-standard install directories
* New command to change the pitch names in a LilyPond document to another
  language
* In Edit-menu:
  * New command to cut a piece of text and assign it to a variable
  * New shortcut to repeat the last entered music expression
  * New shortcut to expand a short string to user-definable pieces of LilyPond
    input. When no shortcut is typed a dialog is opened where shortcuts can
    be chosen and edited.
  * New shortcuts (Alt+Up and Alt+Down) to jump between blank lines, c.q.
    insertion points


## 0.7.4 -- January 31st, 2009

* Translations updated: es, tr, it, nl
* Auto-configures Okular in KDE 4.2 to enable point-and-click
* New Fullscreen option
* New option to disable the built-in PDF preview
* A LogWidget bug fixed that garbled the text if the user clicked somewhere
  in the log while LilyPond was still running
* Some Rumor bugs fixed


## 0.7.3 -- January 22nd, 2009

* Score Wizard: new "Try" button that shows score example
* New rhythm menu actions to copy and paste rhythms
* New option to set default directory for documents
* New option to save state (bookmarks, cursor position, etc.) for documents
* New options to edit keyboard shortcuts and toolbars
* Default keyboard shortcuts have been added for most used actions
* Save Dialog now also has LilyPond filetype filter and default extension
* Bugfixes:
  * Fix editor part not saving and loading settings
  * Score Wizard: fix partial measure, tabstaff, basso continuo and drumstaff
* Installation:
  * Install script does not use pykdeconfig anymore, just tests PyKDE4, etc.
  * Release tarballs now have prebuilt icons and translations


## 0.7.2 -- January 7th, 2009

* New "Run LilyPond" icon (hand drawn in Inkscape, based on the LilyPond XPM)
* Open Current Folder action
* Actions to view or print PDF, play MIDI or email documents
* Bugfixes:
  * Fix shift-up and shift-down selection in editor while PDF is visible.
  * don't say LilyPond crashes if user terminates the process
  * End startup notification if running instance found.


## 0.7.1 -- January 3rd, 2009

* Settings dialog
* Show Path in window title option
* Tools save their settings
* Tool Views submenu in Settings menu
* Fix handling of filenames containing non-ascii characters
* Misc other fixes and improvements


## 0.7 -- December 26th, 2008

* Initial release.

[unreleased]: https://github.com/frescobaldi/frescobaldi/compare/v4.0.3...master
[4.0.3]: https://github.com/frescobaldi/frescobaldi/compare/v4.0.2...v4.0.3
[4.0.2]: https://github.com/frescobaldi/frescobaldi/compare/v4.0.1...v4.0.2
[4.0.1]: https://github.com/frescobaldi/frescobaldi/compare/v4.0.0...v4.0.1
[4.0.0]: https://github.com/frescobaldi/frescobaldi/compare/v3.3.0...v4.0.0
[3.3.0]: https://github.com/frescobaldi/frescobaldi/compare/v3.2...v3.3.0
[3.2]: https://github.com/frescobaldi/frescobaldi/compare/v3.1.3...v3.2
[3.1.3]: https://github.com/frescobaldi/frescobaldi/compare/v3.1.2...v3.1.3
[3.1.2]: https://github.com/frescobaldi/frescobaldi/compare/v3.1.1...v3.1.2
[3.1.1]: https://github.com/frescobaldi/frescobaldi/compare/v3.1...v3.1.1
[3.1]: https://github.com/frescobaldi/frescobaldi/compare/v3.0.0...v3.1
[3.0.0]: https://github.com/frescobaldi/frescobaldi/compare/v2.20.0...v3.0.0
