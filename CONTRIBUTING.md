CONTRIBUTING
============

The Frescobaldi LilyPond sheet music editor is written in Python and uses
Qt for its user interface, via the PyQt bindings.

'frescobaldi' is not a real package: on startup, the absolute
'frescobaldi' directory is added to sys.path and its own __path__ is
cleared so all modules and packages inside frescobaldi are
available as toplevel modules and packages.


Running Frescobaldi in an interactive shell
===========================================

To test features or to experiment, you can run Frescobaldi in an interactive
Python shell. It is recommended to open a shell (e.g. by simply running python
without arguments, or by using Dreampie or IPython) and then enter:

from frescobaldi.debug import *

This ensures the application starts up and also installs some handlers that
print debugging information on certain events. And it imports the most used
modules.


How Frescobaldi is organized
============================

There can be one or more `mainwindow.MainWindow` instances and one or more
`document.Document` instances (when the last Document is closed, another one is
always constructed). The app module keeps references to those and contains the
Signals emitted when something changes.

Many parts inside Frescobaldi need to store or cache additional information or
add features to Documents, MainWindows etc. Instead of clobbering those basic
classes with an ever-growing number of unrelated groups of methods, a different
approach is chosen: the plugin module.

This keeps all classes small and only have methods that directly apply to
themselves and not to other parts of Frescobaldi (separation of concerns).

So e.g. the resultfiles, highlighter or documentinfo modules contain classes
for objects that coexist with a Document, and providing their own relevant
methods, while keeping a weak reference to the Document.

Exchange of messages is done as much as possible using signals (PyQt signals
or from the signals module), or event filters, so adding new features changes as
less existing code as possible.


Some important modules:

main:           Entry point
appinfo:        Information about the application, such as the version
toplevel:       Adds the path of frescobaldi to sys.path, clears __path__
                so all modules inside frescobaldi can be imported as
                toplevel modules and packages
app:            Central hub with global signals, also keeping references to
                mainwindow and document instances
mainwindow:     MainWindow (QMainWindow)
document:       Document (QTextDocument)
view:           View (QPlainTextEdit)
menu:           Here the menubar is constructed (by importing all the relevant
                modules and adding the actions they define)
plugin:         A simple way to extend objects without them knowing it
metainfo:       Stores (optionally) meta information about the document, such
                as last cursor position, whether to enable auto indent, etc
panel:          The base class of all dock widgets
panelmanager:   Add new dock widget tools here
symbols:        Provides icons of LilyPond-generated SVG files that draw
                themselves in the default text color.


Some completely generic modules (don't have anything to do with Frescobaldi or
LilyPond):

signals:        An alternative to Qt signals that allows for connections to have
                priorities, and objects don't have to be Qt objects
cachedproperty: Caches properties that can be asynchronously computed
slexer:         A Stateful Lexer, used to build regular expression-based parsers
hyphenator:     Hyphenate text using hyphenation dictionaries
node:           A list-like type to build tree structures with
cursortools:    Some useful functions manipulating QTextCursor instances
portmidi:       Access the PortMidi library in different ways
midifile:       Load and play MIDI files


Contributing, Coding Style
==========================

A clean pythonic coding style is preferred, with short methods and method names,
and small modules and classes that encapsulate functionality in a sensible way.
See also PEP8 (http://www.python.org/dev/peps/pep-0008/)

Indent: 4 spaces indent with no tabs

Case:   ClassName, module_name, methodname() (or methodName() for classes that
        inherit from Qt classes). Instance attributes that are not meant to be
        used from outside an instance are prefixed with an underscore, e.g.
        self._document.

        There is a habit, inspired by Qt, to use setters and getters for such
        attributes: obj.setDocument(document) and obj.document().

        Names for actions (e.g. file_open) and QSettings keys should always be
        lowercase and use underscores where needed.

Write code so that adding or extending functionality later only adds lines, not
changes or removes existing lines.

Module imports: one per line. First the Python standard library imports, then
PyQt, then the generic Frescobaldi imports and then imports from the current
package. The different groups separated by a blank line:

    import os                       # stdlib imports
    import sys

    from PyQt5.QtCore import ...    # PyQt imports

    import app                      # generic Frescobaldi imports
    import icons

    from . import widget            # imports from current package

Avoid platform specific code, but when it is really needed, you can test
for them:

    if platform.system() == "Linux":
        ...
    elif platform.system() == "Darwin": # macOS
        ...
    elif platform.system() == "Windows":
        ...


Adding Functionality
====================

Separate out core functionality from its GUI. Put core functionality in a basic
module. For the GUI preferably make a new package/__init__.py, importing that
e.g. from menu.py while constructing the GUI. An example is the documentwatcher
base module, it automatically watches open documents on disk, simply by
listening to signals sent from app. It sends a documentChanged() signal when
something happens, nothing else. The externalchanges package that gets imported
from mainwindow.py, starts up the documentwatcher if the user has it enabled.

So the documentwatcher watcher is a module just capable of performing a task,
without needing to have logic for accessing the preferences, constructing a
particular GUI, etc. It could, like app and many other modules, be used almost
unchanged in any other application.

New features that add menu actions can be imported in menu.py, while building
the menu. Features that should run in a global background thread can have their
toplevel file (<feature>/__init__.py) imported from main.py or mainwindow.py,
loading as few as possible on first import.


Preparing patches or Pull Requests
==================================

When preparing a patch or pull request, please add new functionality first.
Old functionality that is superseded by the newer functions can be removed later
when the new functionality has been tested thoroughly. Change existing files
as less as possible. Preferably add new files and packages.

User Interface strings that are meant to be translated should be wrapped in
_("Message Text") constructs. See also [TRANSLATIONS.md](TRANSLATIONS.md) for
vital information about how to use the translation mechanism and how to use
variables inside messages.

Objects that are longer-lived should be able to retranslate their GUIs. This can
be done by adding a method named translateUI(self), in which you set the texts
to the user interface objects, and calling app.translateUI() at the end of the
constructor. Frescobaldi will call your translateUI() method once and also take
care of calling it again when the user changes the UI language in the
preferences. You can also do this directly by connecting the method that sets
the texts to the app.languageChanged signal.


Guidelines for writing GUI texts
================================

* Write short, directly and non-technical
* For help pages: each paragraph is one translatable string
* Avoid HTML in texts (but <code>\include</code> is OK)
* In help pages you can construct HTML using some helper functions
* Avoid hard line breaks (<br>) in any texts: use short paragraphs instead
* Use named format fields: not "page {0} of {1}" but "page {num} of {total}"
* Don't change existing strings just for cosmetics, it breaks translations


New release checklist
=====================

Checklist before making a new release:

- Bump the version in `frescobaldi/appinfo.py`.
- Add the release date in `CHANGELOG.md` and `linux/org.frescobaldi.Frescobaldi.metainfo.xml.in`.
- Update the list of contributors in `frescobaldi/userguide/credits.md`.
