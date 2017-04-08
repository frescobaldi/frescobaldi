# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Builtin snippets.
"""


import builtins
import collections

# postpone translation
_ = lambda *args: lambda: builtins._(*args)


T = collections.namedtuple("Template", "title text")


builtin_snippets = {

'blankline': T(_("Blank Line"),
r"""
$CURSOR
"""),


'removelines': T(_("Delete Line(s)"),
r"""-*- python;

import cursortools

def main():
    start = end = cursortools.block(cursor)
    while end.position() + end.length() < cursor.selectionEnd():
        end = end.next()
    cursor.setPosition(start.position())
    cursor.setPosition(end.position(), cursor.KeepAnchor)
    cursor.movePosition(cursor.EndOfBlock, cursor.KeepAnchor)
    cursor.movePosition(cursor.NextBlock, cursor.KeepAnchor)
    cursor.removeSelectedText()

"""),


'remove_matching_pair': T(_("Delete Matching Pair"),
r"""-*- python; indent: no;

import cursortools
import matcher

def main():
    cursors = matcher.matches(cursor)
    if cursors:
        with cursortools.compress_undo(cursor):
            for c in cursors:
                c.removeSelectedText()

"""),


'next_blank_line': T(_("Next Blank Line"),
r"""-*- python; indent: no;

import cursortools

def main():
    block = cursortools.next_blank(cursor.block())
    if block:
        cursor.setPosition(block.position() + block.length() - 1)
        return cursor

"""),


'previous_blank_line': T(_("Previous Blank Line"),
r"""-*- python; indent: no;

import cursortools

def main():
    block = cursortools.previous_blank(cursor.block())
    if block:
        cursor.setPosition(block.position() + block.length() - 1)
        return cursor

"""),


'next_blank_line_select': T(_("Select until Next Blank Line"),
r"""-*- python; indent: no;

import cursortools

def main():
    block = cursortools.next_blank(cursor.block())
    if block:
        cursor.setPosition(block.position() + block.length() - 1, cursor.KeepAnchor)
        return cursor

"""),


'previous_blank_line_select': T(_("Select until Previous Blank Line"),
r"""-*- python; indent: no;

import cursortools

def main():
    block = cursortools.previous_blank(cursor.block())
    if block:
        cursor.setPosition(block.position() + block.length() - 1, cursor.KeepAnchor)
        return cursor

"""),


'quotes_s': T(_("Single Typographical Quotes"),
"""-*- menu: text; python;
import lasptyqu
left, right = lasptyqu.preferred().secondary
if text:
    text = left + text + right
else:
    text = [left, CURSOR, right]
"""),


'quotes_d': T(_("Double Typographical Quotes"),
"""-*- menu: text; python;
import lasptyqu
left, right = lasptyqu.preferred().primary
if text:
    text = left + text + right
else:
    text = [left, CURSOR, right]
"""),


'voice1': T(None,
r"""-*- name: v1;
\voiceOne"""),


'voice2': T(None,
r"""-*- name: v2;
\voiceTwo"""),


'voice3': T(None,
r"""-*- name: v3;
\voiceThree"""),


'voice4': T(None,
r"""-*- name: v4;
\voiceFour"""),


'1voice': T(None,
r"""-*- name: 1v;
\oneVoice"""),


'stanza1': T(None,
r"""-*- name: s1;
\set stanza = "1."
"""),


'stanza2': T(None,
r"""-*- name: s2;
\set stanza = "2."
"""),


'stanza3': T(None,
r"""-*- name: s3;
\set stanza = "3."
"""),


'stanza4': T(None,
r"""-*- name: s4;
\set stanza = "4."
"""),


'stanza5': T(None,
r"""-*- name: s5;
\set stanza = "5."
"""),


'stanza6': T(None,
r"""-*- name: s6;
\set stanza = "6."
"""),


'times23': T(_("Tuplets"),
r"""-*- menu: blocks; selection: strip;
\tuplet 3/2 { $SELECTION }"""),


'onceoverride': T(None,
r"""-*- name: oo;
\once \override """),


'm22': T(_("Modern 2/2 Time Signature"),
r"""-*- name: 22;
\numericTimeSignature
\time 2/2"""),


'm44': T(_("Modern 4/4 Time Signature"),
r"""-*- name: 44;
\numericTimeSignature
\time 4/4"""),


'tactus': T(_("Tactus Time Signature (number with note)"),
r"""-*- name: tac;
\once \override Staff.TimeSignature #'style = #'()
\once \override Staff.TimeSignature #'stencil = #ly:text-interface::print
\once \override Staff.TimeSignature #'text = \markup {
  \override #'(baseline-skip . 0.5)
  \column { \number $CURSOR1$ANCHOR \tiny \note #"2" #-.6 }
}
"""),


'ly_version': T(_("LilyPond Version"),
r"""-*- menu;
\version "$LILYPOND_VERSION"
"""),


'repeat': T(_("Repeat"),
r"""-*- menu: blocks; name: rep; selection: strip; symbol: bar_repeat_start;
\repeat volta 2 { $SELECTION }"""),

'repeatunfold': T(_("Repeat unfold"),
r"""-*- menu: blocks; name: repunf; selection: strip;
\repeat unfold 2$CURSOR { $SELECTION }"""),

'relative': T(_("Relative Music"),
r"""-*- name: rel;
\relative c$CURSOR'$ANCHOR {
""" '   $SELECTION' r"""
}"""),


'score': T(None,
r"""-*- menu: blocks;
\score {
  $SELECTION
  \layout {}
  \midi {}
}
"""),


'uppercase': T(_("Upper case selection"),
r"""-*- python; selection: yes, keep;
text = text.upper()
"""),


'lowercase': T(_("Lower case selection"),
r"""-*- python; selection: yes, keep;
text = text.lower()
"""),


'titlecase': T(_("Title case selection"),
r"""-*- python; selection: yes, keep;
text = text.title()
"""),


'markup': T(_("Markup"),
r"""-*- name: m; selection: strip;
\markup { $SELECTION }"""),


'markup_lines_selection': T(_("Markup lines"),
r"""-*- name: l; python; selection: yes, keep, strip;
text = '\n'.join(r'\line { %s }' % l for l in text.splitlines())
if state[-1] != 'markup':
    text = '\\markup {\n%s\n}' % text
"""),


'markup_column': T(_("Markup column"),
r"""-*- name: c; selection: yes, keep, strip;
\column { $SELECTION }"""),


'tagline_date_version': T(_("Tagline with date and LilyPond version"),
r"""tagline = \markup {
  Engraved at
  \simple #(strftime "%Y-%m-%d" (localtime (current-time)))
  with \with-url #"http://lilypond.org/"
  \line { LilyPond \simple #(lilypond-version) (http://lilypond.org/) }
}
"""),


'header': T(_("Header Template"),
r"""-*- name: h; menu: blocks;
\header {
  title = "$CURSOR"
  composer = ""
  tagline = \markup {
    Engraved at
    \simple #(strftime "%Y-%m-%d" (localtime (current-time)))
    with \with-url #"http://lilypond.org/"
    \line { LilyPond \simple #(lilypond-version) (http://lilypond.org/) }
  }
}
"""),


'no_tagline': T(_("No Tagline"),
r"""-*- name: nt; python; menu: properties;
text = 'tagline = ##f'
if state[-1] != 'header':
    text = '\\header {\n%s\n}' % text
"""),


'no_barnumbers': T(_("No Barnumbers"),
r"""-*- name: nb; python; menu: properties;
text = r'\remove "Bar_number_engraver"'
if state[-1] not in ('context', 'with'):
    text = '\\context {\n\\Score\n%s\n}' % text
    if state[-1] != 'layout':
        text = '\\layout {\n%s\n}' % text
"""),


'midi_tempo': T(_("Midi Tempo"),
r"""-*- name: mt; python;
text = ['tempoWholesPerMinute = #(ly:make-moment ', CURSOR, '100 4)']
if state[-1] not in ('context', 'with'):
    text = ['\\context {\n\\Score\n'] + text + ['\n}']
    if state[-1] != 'midi':
        text = ['\\midi {\n'] + text + ['\n}']
"""),


'staff_size': T(_("Staff Size"),
r"""-*- name: ss; python;
if state[-1] == 'music':
    text = (
        "\\set Staff.fontSize = #-1\n"
        "\\override Staff.StaffSymbol #'staff-space = #(magstep -1)\n")
else:
    text = (
        "fontSize = #-1\n"
        "\\override StaffSymbol #'staff-space = #(magstep -1)")
    if state[-1] == 'new':
        text = '\\with {\n%s\n}' % text
    elif state[-1] not in ('context', 'with'):
        text = '\\context {\n\\Staff\n%s\n}' % text
        if state[-1] != 'layout':
            text = '\\layout {\n%s\n}' % text
"""),


'double': T(_("Double selection or current line"),
r"""-*- python; indent: no;
def main():
    if not cursor.hasSelection():
        while not cursor.block().text() or cursor.block().text().isspace():
            if not cursor.movePosition(cursor.PreviousBlock):
                break
        cursor.movePosition(cursor.StartOfBlock)
        if not cursor.movePosition(cursor.NextBlock, cursor.KeepAnchor):
            cursor.movePosition(cursor.EndOfBlock, cursor.KeepAnchor)
            t = '\n' + cursor.selection().toPlainText() + '\n'
        else:
            t = cursor.selection().toPlainText()
    else:
        t = cursor.selection().toPlainText()
    cursor.setPosition(cursor.selectionEnd())
    cursor.clearSelection()
    cursor.insertText(t)
    if t.endswith('\n'):
        cursor.movePosition(cursor.Left)
    return cursor
"""),


'comment': T(_("snippet: add comment characters", "Comment"),
r"""-*- python; indent: no; menu: comment;

# get text before and after the selection
import cursortools
before, text, after = cursortools.partition(cursor)

# determine state
for s in state[::-1]:
    if s in ('lilypond', 'html', 'scheme'):
        break
else:
    s = 'lilypond'

def html():
    if text:
        return '<!-- ' + text + ' -->'
    else:
        return ['<!-- ', CURSOR, ' -->']

def lilypond():
    if '\n' in text:
        if text.endswith('\n'):
            return '% ' + text[:-1].replace('\n', '\n% ') + '\n'
        elif after and not after.isspace():
            return '%{ ' + text + '%} '
        else:
            return '% ' + text.replace('\n', '\n% ')
    elif text:
        if after and not after.isspace():
            return '%{ ' + text + '%} '
        else:
            return '% ' + text + after
    else:
        return '% '

def scheme():
    if text:
        return '; ' + text.replace('\n', '\n; ')
    else:
        return '; '

if s == 'lilypond':
    text = lilypond()
elif s == 'html':
    text = html()
elif s == 'scheme':
    text = scheme()

"""),


'uncomment': T(_("snippet: remove comment characters", "Uncomment"),
r"""-*- python; indent: no; menu: comment;
import re

def main():
    text = globals()['text']
    # determine state
    for s in state[::-1]:
        if s in ('lilypond', 'html', 'scheme'):
            break
    else:
        s = 'lilypond'

    def html(text):
        if text:
            text = text.replace('<!-- ', '')
            text = text.replace(' -->', '')
            text = text.replace('<!--', '')
            text = text.replace('-->', '')
            return text

    def lilypond(text):
        if text.lstrip().startswith('%{'):
            if text.lstrip().startswith('%{ '):
                text = text.lstrip()[3:]
            else:
                text = text.lstrip()[2:]
            if text.rstrip().endswith('%}'):
                text = text.rstrip()[:-2]
        else:
            if not text:
                cursor.select(cursor.BlockUnderCursor)
                text = cursor.selection().toPlainText()
            text = re.compile(r'^(\s*)%+ ?', re.M).sub(r'\1', text)
        return text

    def scheme(text):
        return re.compile(r'^(\s*);+', re.M).sub(r'\1', text)

    if s == 'lilypond':
        text = lilypond(text)
    elif s == 'html':
        text = html(text)
    elif s == 'scheme':
        text = scheme(text)

    if text != cursor.selection().toPlainText():
        cursor.insertText(text)

"""),


'paper_a5': T(_("A5 Paper"),
r"""-*- name: a5; python;
text = r'#(set-paper-size "a5")'
if state[-1] != 'paper':
    text = '\\paper {\n%s\n}' % text
"""),


'document_fonts': T(_("Document Fonts..."),
r"""-*- menu: paper; name: fo; python; icon: preferences-desktop-font;
snippet = '''\
fonts = #
(make-pango-font-tree
  "{roman}"
  "{sans}"
  "{typewriter}"
  (/ (* staff-height pt) 2.5))
'''

import globalfontdialog
dlg = globalfontdialog.GlobalFontDialog(view)
if dlg.exec_():
    text = snippet.format(
        roman = dlg.romanFont(),
        sans = dlg.sansFont(),
        typewriter = dlg.typewriterFont())
    if state[-1] != "paper":
        text = "\\paper {{\n{0}}}\n".format(text)

"""),


'last_note': T(_("Last note or chord"),
r"""-*- python; menu: music; symbol: note_ellipsis;
# This snippet reads back the last entered note or chord and
# inserts it again. It removes the octave mark from a note of the first
# note of a chord if the music is in relative mode.

import lydocument
import ly.lex.lilypond as lp

# space needed before cursor?
block = cursor.document().findBlock(cursor.selectionStart())
beforecursor = block.text()[:cursor.selectionStart()-block.position()]
spaceneeded = bool(beforecursor and beforecursor[-1] not in "\t ")

chordstart, chordend = None, None
notestart = None
relative = False
found = False

c = lydocument.cursor(cursor)
runner = lydocument.Runner.at(c, True)

for t in runner.backward():
    if t == '\\relative':
        relative = True
        break
    elif isinstance(t, (lp.Score, lp.Book, lp.BookPart, lp.Name)):
        break
    if found:
        continue
    if chordend is not None:
        if isinstance(t, lp.ChordStart):
            chordstart = runner.position()
            found = True
        continue
    if isinstance(t, lp.ChordEnd):
        chordend = runner.position() + len(t)
    elif isinstance(t, lp.Note) and t not in ('R' ,'q', 's', 'r'):
        notestart = runner.position()
        found = True

if found:
    if chordstart is not None:
        text = []
        removeOctave = 1 if relative else 0
        c.start, c.end = chordstart, chordend
        for t in lydocument.Source(c):
            # remove octave from first pitch in relative
            if isinstance(t, lp.Note):
                removeOctave -= 1
            elif isinstance(t, lp.Octave) and removeOctave == 0:
                continue
            text.append(t)
        text = ''.join(text)
    elif notestart is not None:
        text = []
        c.start, c.end = notestart, None
        for t in lydocument.Source(c):
            if isinstance(t, lp.Note):
                text.append(t)
            elif not relative and isinstance(t, lp.Octave):
                text.append(t)
            else:
                break
        text = ''.join(text)
    if spaceneeded:
        text = " " + text
"""),


'color_dialog': T(_("Color"),
r"""-*- name: col; python; icon: applications-graphics;

# Insert a color from a dialog


import inputdialog
colors = {
    (0, 0, 0): "black",
    (255, 255, 255): "white",
    (255, 0, 0): "red",
    (0, 255, 0): "green",
    (0, 0, 255): "blue",
    (0, 255, 255): "cyan",
    (255, 0, 255): "magenta",
    (255, 255, 0): "yellow",
    (128, 128, 128): "grey",
    (128, 0, 0): "darkred",
    (0, 128, 0): "darkgreen",
    (0, 0, 128): "darkblue",
    (0, 128, 128): "darkcyan",
    (128, 0, 128): "darkmagenta",
    (128, 128, 0): "darkyellow",
}

color = inputdialog.getColor(view)
if color is not None:
    rgb = color.getRgb()[:-1]

    if rgb in colors:
        text = '#' + colors[rgb]
    else:
        rgb = tuple(map(lambda v: format(v / 255.0, ".4"), rgb))
        text = "#(rgb-color {0} {1} {2})".format(*rgb)
"""),


'template_leadsheet': T(_("Basic Leadsheet"),
r"""-*- template; template-run;
\version "$LILYPOND_VERSION"

\header {
  title = ""
}

global = {
  \time 4/4
  \key c \major
  \tempo 4=100
}

chordNames = \chordmode {
  \global
  c1

}

melody = \relative c'' {
  \global
  c4 d e f
  $CURSOR
}

words = \lyricmode {


}

\score {
  <<
    \new ChordNames \chordNames
    \new FretBoards \chordNames
    \new Staff { \melody }
    \addlyrics { \words }
  >>
  \layout { }
  \midi { }
}
"""),


'template_choir_hymn': T(_("Choir Hymn"),
r"""-*- template; template-run;
\version "$LILYPOND_VERSION"

\header {
  title = ""
}

global = {
  \time 4/4
  \key c \major
  \tempo 4=100
}

soprano = \relative c'' {
  \global
  $CURSORc4

}

alto = \relative c' {
  \global
  c4

}

tenor = \relative c' {
  \global
  c4

}

bass = \relative c {
  \global
  c4

}

verseOne = \lyricmode {
  \set stanza = "1."
  hi

}

verseTwo = \lyricmode {
  \set stanza = "2."
  ha

}

verseThree = \lyricmode {
  \set stanza = "3."
  ho

}

\score {
  \new ChoirStaff <<
    \new Staff \with {
      midiInstrument = "choir aahs"
      instrumentName = \markup \center-column { S A }
    } <<
      \new Voice = "soprano" { \voiceOne \soprano }
      \new Voice = "alto" { \voiceTwo \alto }
    >>
    \new Lyrics \with {
      \override VerticalAxisGroup #'staff-affinity = #CENTER
    } \lyricsto "soprano" \verseOne
    \new Lyrics \with {
      \override VerticalAxisGroup #'staff-affinity = #CENTER
    } \lyricsto "soprano" \verseTwo
    \new Lyrics \with {
      \override VerticalAxisGroup #'staff-affinity = #CENTER
    } \lyricsto "soprano" \verseThree
    \new Staff \with {
      midiInstrument = "choir aahs"
      instrumentName = \markup \center-column { T B }
    } <<
      \clef bass
      \new Voice = "tenor" { \voiceOne \tenor }
      \new Voice = "bass" { \voiceTwo \bass }
    >>
  >>
  \layout { }
  \midi { }
}
"""),


}

