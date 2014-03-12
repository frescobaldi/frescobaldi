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
LilyPond DOM

(c) 2008-2011 Wilbert Berendsen
License: GPL.

A simple Document Object Model for LilyPond documents.

The purpose is to easily build a LilyPond document with good syntax,
not to fully understand all features LilyPond supports. (This DOM does
not enforce a legal LilyPond file.)

All elements of a LilyPond document inherit Node.

Note: elements keep a weak reference to their parent.

"""

from __future__ import unicode_literals
from __future__ import absolute_import # prevent picking old stale node.py from package

import fractions
import re

import node

import ly.pitch
import ly.duration


class LyNode(node.WeakNode):
    """
    Base class for LilyPond objects, based on Node,
    which takes care of the tree structure.
    """
    
    ##
    # True if this element is single LilyPond atom, word, note, etc.
    # When it is the only element inside { }, the brackets can be removed.
    isAtom = False
   
    ##
    # The number of newlines this object wants before it.
    before = 0
    
    ##
    # The number of newlines this object wants after it.
    after = 0
    
    def ly(self, printer):
        """
        Returns printable output for this object.
        Can ask printer for certain settings, e.g. pitch language etc.
        """
        return ''

    def concat(self, other):
        """
        Returns a string with newlines to concat this node to another one.
        If zero newlines are requested, an empty string is returned.
        """
        return '\n' * max(self.after, other.before)


##
# Leaf and Container are the two base classes the rest of the LilyPond
# element classes is based on.
# 
class Leaf(LyNode):
    """ A leaf node without children """
    pass


class Container(LyNode):
    """ A node that concatenates its children on output """
    
    ##
    # default character to concatenate children with
    defaultSpace = " "
    
    @property
    def before(self):
        if len(self):
            return self[0].before
        else:
            return 0

    @property
    def after(self):
        if len(self):
            return self[-1].after
        else:
            return 0
            
    def ly(self, printer):
        if len(self) == 0:
            return ''
        else:
            n = self[0]
            res = [n.ly(printer)]
            for m in self[1:]:
                res.append(n.concat(m) or self.defaultSpace)
                res.append(m.ly(printer))
                n = m
            return "".join(res)


##
# Helper classes
#
class Printer(object):
    """
    Performs certain operations on behalf of a LyNode tree,
    like quoting strings or translating pitch names, etc.
    """
    def __init__(self):
        self.typographicalQuotes = True
        self.language = "nederlands"
        self.indentString = '  '
        
    def quoteString(self, text):
        if self.typographicalQuotes:
            text = re.sub(r'"(.*?)"', '\u201C\\1\u201D', text)
            text = re.sub(r"'(.*?)'", '\u2018\\1\u2019', text)
            text = text.replace("'", '\u2018')
        # escape regular double quotes
        text = text.replace('"', '\\"')
        # quote the string
        return '"{0}"'.format(text)

    def indentGen(self, node, startIndent = 0):
        """
        A generator that walks on the output of the given node,
        and returns properly indented LilyPond code.
        """
        d = startIndent
        for t in node.ly(self).splitlines() + [''] * node.after:
            if d and re.match(r'#?}|>|%}', t):
                d -= 1
            yield self.indentString * d + t
            if re.search(r'(\{|<|%{)$', t):
                d += 1

    def indent(self, node):
        """
        Return a formatted printout of node (and its children)
        """
        return '\n'.join(self.indentGen(node))


class Reference(object):
    """
    A simple object that keeps a name, to use as a (context)
    identifier. Set the name attribute to the name you want
    to display, and on all places in the document the name
    will show up.
    """
    def __init__(self, name=""):
        self.name = name
    
    def __unicode__(self):
        return self.name


class Named(object):
    """
    Mixin to print a \\name before the contents of the container.
    unicode() is called on the self.name attribute, so it may also
    be a Reference.
    """
    name = ""
    
    def ly(self, printer):
        return "\\{0} {1}".format(unicode(self.name), super(Named, self).ly(printer))
        
        
class HandleVars(object):
    """
    A powerful mixin class that makes handling unique variable assignments
    inside a Container more easy.
    E.g.:
    >>> h = Header()
    >>> h['composer'] = "Johann Sebastian Bach"
    creates a subnode (by default Assignment) with the name 'composer', and
    that node again gets an autogenerated subnode of type QuotedString (If the
    argument wasn't already a Node).
    """
    childClass = None # To be filled in later

    def ifbasestring(func):
        """
        Ensure that the method is only called for basestring objects.
        Otherwise the same method from the super class is called.
        """
        def newfunc(obj, name, *args):
            if isinstance(name, basestring):
                return func(obj, name, *args)
            else:
                f = getattr(super(HandleVars, obj), func.func_name)
                return f(name, *args)
        return newfunc

    @ifbasestring
    def __getitem__(self, name):
        for node in self.find_children(self.childClass, 1):
            if node.name == name:
                return node

    @ifbasestring
    def __setitem__(self, name, valueObj):
        if not isinstance(valueObj, LyNode):
            valueObj = self.importNode(valueObj)
        assignment = self[name]
        if assignment:
            assignment.setValue(valueObj)
        else:
            self.childClass(name, self, valueObj)

    @ifbasestring
    def __contains__(self, name):
        return bool(self[name])

    @ifbasestring
    def __delitem__(self, name):
        h = self[name]
        if h:
            self.remove(h)

    def importNode(self, obj):
        """
        Try to interpret the object and transform it into a Node object
        of the right species.
        """
        return QuotedString(obj)


class AddDuration(object):
    """ Mixin to add a duration (as child). """
    def ly(self, printer):
        s = super(AddDuration, self).ly(printer)
        dur = self.find_child(Duration, 1)
        if dur:
            s += dur.ly(printer)
        return s


class Block(Container):
    """ 
    A vertical container type that puts everything on a new line.
    """
    defaultSpace = "\n"
    before, after = 1, 1


class Document(Container):
    """ 
    A container type that puts everything on a new line.
    To be used as a full LilyPond document.
    """
    defaultSpace = "\n"
    after = 1


##
# These classes correspond to real LilyPond data.
#
class Text(Leaf):
    """ A leaf node with arbitrary text """
    def __init__(self, text="", parent=None):
        super(Text, self).__init__(parent)
        if not isinstance(text, basestring):
            text = unicode(text)
        self.text = text
    
    def ly(self, printer):
        return self.text


class TextDur(AddDuration, Text):
    """ A text note with an optional duration as child. """
    pass


class Line(Text):
    """ A text node that claims its own line. """
    before, after = 1, 1
    
    
class Comment(Text):
    """ A LilyPond comment at the end of a line """
    after = 1

    def ly(self, printer):
        return re.compile('^', re.M).sub('% ', self.text)


class LineComment(Comment):
    """ A LilyPond comment that takes a full line """
    before = 1
        

class BlockComment(Comment):
    """ A block comment between %{ and %} """
    @property
    def before(self):
        return '\n' in self.text and 1 or 0
    
    @property
    def after(self):
        return '\n' in self.text and 1 or 0
        
    def ly(self, printer):
        text = self.text.replace('%}', '')
        f = "%{{\n{0}\n%}}" if '\n' in text else "%{{ {0} %}}"
        return f.format(text)
            

class QuotedString(Text):
    """ A string that is output inside double quotes. """
    isAtom = True
    def ly(self, printer):
        return printer.quoteString(self.text)
    

class Newline(LyNode):
    """ A newline. """
    after = 1


class BlankLine(Newline):
    """ A blank line. """
    before = 1
        

class Scheme(Text):
    """ A Scheme expression, without the extra # prepended """
    isAtom = True
    
    def ly(self, printer):
        return '#' + self.text


class Version(Line):
    """ a LilyPond version instruction """
    def ly(self, printer):
        return r'\version "{0}"'.format(self.text)


class Include(Line):
    """ a LilyPond \\include statement """
    def ly(self, printer):
        return r'\include "{0}"'.format(self.text)


class Assignment(Container):
    """
    A varname = value construct with it's value as its first child
    The name can be a string or a Reference object: so that everywhere
    where this varname is referenced, the name is the same.
    """
    before, after = 1, 1
    
    def __init__(self, name=None, parent=None, valueObj=None):
        super(Assignment, self).__init__(parent)
        self.name = name
        if valueObj:
            self.append(valueObj)
    
    # Convenience methods:
    def setValue(self, obj):
        if len(self):
            self[0] = obj
        else:
            self.append(obj)

    def value(self):
        if len(self):
            return self[0]

    def ly(self, printer):
        return "{0} = {1}".format(
            unicode(self.name), super(Assignment, self).ly(printer))


HandleVars.childClass = Assignment


class Identifier(Leaf):
    """
    An identifier, prints as \\name.
    Name may be a string or a Reference object.
    """
    isAtom = True
    
    def __init__(self, name=None, parent=None):
        super(Identifier, self).__init__(parent)
        self.name = name
        
    def ly(self, printer):
        return "\\" + unicode(self.name)


class Statement(Named, Container):
    """
    Base class for statements with arguments. The statement is read in the
    name attribute, the arguments are the children.
    """
    before = 0 # do not read property from container
    isAtom = True


class Command(Statement):
    """
    Use this to create a LilyPond command supplying the name (or a Reference)
    when instantiating.
    """
    def __init__(self, name, parent=None):
        super(Command, self).__init__(parent)
        self.name = name

    
class Enclosed(Container):
    """
    Encloses all children between brackets: { ... }
    If may_remove_brackets is True in subclasses, the brackets are
    removed if there is only one child and that child is an atom (i.e.
    a single LilyPond expression.
    """
    may_remove_brackets = False
    pre, post = "{", "}"
    before, after = 0, 0
    isAtom = True
    
    def ly(self, printer):
        if len(self) == 0:
            return " ".join((self.pre, self.post))
        sup = super(Enclosed, self)
        text = sup.ly(printer)
        if self.may_remove_brackets and len(self) == 1 and self[0].isAtom:
            return text
        elif sup.before or sup.after or '\n' in text:
            return "".join((self.pre, "\n" * max(sup.before, 1), text,
                                      "\n" * max(sup.after, 1), self.post))
        else:
            return " ".join((self.pre, text, self.post))


class Seq(Enclosed):
    """ An SequentialMusic expression between { } """
    pre, post = "{", "}"
    

class Sim(Enclosed):
    """ An SimultaneousMusic expression between << >> """
    pre, post = "<<", ">>"


class Seqr(Seq): may_remove_brackets = True
class Simr(Sim): may_remove_brackets = True
    

class SchemeLily(Enclosed):
    """ A LilyPond expression between #{ #} (inside scheme) """
    pre, post = "#{", "#}"


class SchemeList(Enclosed):
    """ A list of items enclosed in parentheses """
    pre, post = "(", ")"
    
    def ly(self, printer):
        return self.pre + super(Enclosed, self).ly(printer) + self.post


class StatementEnclosed(Named, Enclosed):
    """
    Base class for LilyPond commands that have a single bracket-enclosed
    list of arguments.
    """
    may_remove_brackets = True


class CommandEnclosed(StatementEnclosed):
    """
    Use this to print LilyPond commands that have a single 
    bracket-enclosed list of arguments. The command name is supplied to
    the constructor.
    """
    def __init__(self, name, parent=None):
        super(CommandEnclosed, self).__init__(parent)
        self.name = name
        
        
class Section(StatementEnclosed):
    """
    Very much like a Statement. Use as base class for \\book { }, \\score { }
    etc. By default never removes the brackets and always starts on a new line.
    """
    may_remove_brackets = False
    before, after = 1, 1


class Book(Section): name = 'book'
class BookPart(Section): name = 'bookpart'
class Score(Section): name = 'score'
class Paper(HandleVars, Section): name = 'paper'
class Layout(HandleVars, Section): name = 'layout'
class Midi(HandleVars, Section): name = 'midi'
class Header(HandleVars, Section): name = 'header'


class With(HandleVars, Section):
    """ If this item has no children, it prints nothing. """
    name = 'with'
    before, after = 0, 0
    
    def ly(self, printer):
        if len(self):
            return super(With, self).ly(printer)
        else:
            return ''


class ContextName(Text):
    """
    Used to print a context name, like \\Score.
    """
    def ly(self, printer):
        return "\\" + self.text


class Context(HandleVars, Section):
    """
    A \\context section for use inside Layout or Midi sections.
    """
    name = 'context'
    
    def __init__(self, contextName="", parent=None):
        super(Context, self).__init__(parent)
        if contextName:
            ContextName(contextName, self)
            

class ContextType(Container):
    """
    \\new or \\context Staff = 'bla' \\with { } << music >>

    A \\with (With) element is added automatically as the first child as soon
    as you use our convenience methods that manipulate the variables
    in \\with. If the \\with element is empty, it does not print anything.
    You should add one other music object to this.
    """
    before, after = 1, 1
    isAtom = True
    ctype = None
    
    def __init__(self, cid=None, new=True, parent=None):
        super(ContextType, self).__init__(parent)
        self.new = new
        self.cid = cid
        
    def ly(self, printer):
        res = []
        res.append(self.new and "\\new" or "\\context")
        res.append(self.ctype or self.__class__.__name__)
        if self.cid:
            res.append("=")
            res.append(printer.quoteString(unicode(self.cid)))
        res.append(super(ContextType, self).ly(printer))
        return " ".join(res)
        
    def getWith(self):
        """
        Gets the attached with clause. Creates it if not there.
        """
        for node in self:
            if isinstance(node, With):
                return node
        self.insert(0, With())
        return self[0]

    def addInstrumentNameEngraverIfNecessary(self):
        """
        Adds the Instrument_name_engraver to the node if it would need it
        to print instrument names.
        """
        if not isinstance(self,
            (Staff, RhythmicStaff, PianoStaff, Lyrics, FretBoards)):
            Line('\\consists "Instrument_name_engraver"', self.getWith())


class ChoirStaff(ContextType): pass
class ChordNames(ContextType): pass
class CueVoice(ContextType): pass
class Devnull(ContextType): pass
class DrumStaff(ContextType): pass
class DrumVoice(ContextType): pass
class Dynamics(ContextType): pass
class FiguredBass(ContextType): pass
class FretBoards(ContextType): pass
class Global(ContextType): pass
class GrandStaff(ContextType): pass
class GregorianTranscriptionStaff(ContextType): pass
class GregorianTranscriptionVoice(ContextType): pass
class InnerChoirStaff(ContextType): pass
class InnerStaffGroup(ContextType): pass
class Lyrics(ContextType): pass
class MensuralStaff(ContextType): pass
class MensuralVoice(ContextType): pass
class NoteNames(ContextType): pass
class PianoStaff(ContextType): pass
class RhythmicStaff(ContextType): pass
class ScoreContext(ContextType):
    """
    Represents the Score context in LilyPond, but the name would
    collide with the Score class that represents \\score { } constructs.

    Because the latter is used more often, use ScoreContext to get
    \\new Score etc.
    """
    ctype = 'Score'

class Staff(ContextType): pass
class StaffGroup(ContextType): pass
class TabStaff(ContextType): pass
class TabVoice(ContextType): pass
class VaticanaStaff(ContextType): pass
class VaticanaVoice(ContextType): pass
class Voice(ContextType): pass


class UserContext(ContextType):
    """
    Represents a context the user creates.
    e.g. \\new MyStaff = cid << music >>
    """
    def __init__(self, ctype, cid=None, new=True, parent=None):
        super(UserContext, self).__init__(cid, new, parent)
        self.ctype = ctype


class ContextProperty(Leaf):
    """
    A Context.property or Context.layoutObject construct.
    Call e.g. ContextProperty('aDueText', 'Staff') to get 'Staff.aDueText'.
    """
    def __init__(self, prop, context=None, parent=None):
        self.prop = prop
        self.context = context

    def ly(self, printer):
        if self.context:
            # In \lyrics or \lyricmode: put spaces around dot.
            p = self.find_parent(InputMode)
            if p and isinstance(p, LyricMode):
                f = '{0} . {1}'
            else:
                f = '{0}.{1}'
            return f.format(self.context, self.prop)
        else:
            return self.prop


class InputMode(StatementEnclosed):
    """
    The abstract base class for input modes such as lyricmode/lyrics,
    chordmode/chords etc.
    """
    pass


class ChordMode(InputMode): name = 'chordmode'
class InputChords(ChordMode): name = 'chords'
class LyricMode(InputMode): name = 'lyricmode'
class InputLyrics(LyricMode): name = 'lyrics'
class NoteMode(InputMode): name = 'notemode'
class InputNotes(NoteMode): name = 'notes'
class FigureMode(InputMode): name = 'figuremode'
class InputFigures(FigureMode): name = 'figures'
class DrumMode(InputMode): name = 'drummode'
class InputDrums(DrumMode): name = 'drums'


class AddLyrics(InputLyrics): 
    name = 'addlyrics'
    may_remove_brackets = False
    before, after = 1, 1


class LyricsTo(LyricMode):
    name = 'lyricsto'
    
    def __init__(self, cid, parent=None):
        super(LyricsTo, self).__init__(parent)
        self.cid = cid
    
    def ly(self, printer):
        res = ["\\" + self.name]
        res.append(printer.quoteString(unicode(self.cid)))
        res.append(super(Named, self).ly(printer))
        return " ".join(res)
        

class Pitch(Leaf):
    """
    A pitch with octave, note, alter.
    octave is specified by an integer, zero for the octave containing middle C.
    note is a number from 0 to 6, with 0 corresponding to pitch C and 6
    corresponding to pitch B.
    alter is the number of whole tones for alteration (can be int or Fraction)
    """

    def __init__(self, octave=0, note=0, alter=0, parent=None):
        super(Pitch, self).__init__(parent)
        self.octave = octave
        self.note = note
        self.alter = fractions.Fraction(alter)

    def ly(self, printer):
        """
        Print the pitch in the preferred language.
        """
        p = ly.pitch.pitchWriter(printer.language)(self.note, self.alter)
        if self.octave < -1:
            return p + ',' * (-self.octave - 1)
        elif self.octave > -1:
            return p + "'" * (self.octave + 1)
        return p


class Duration(Leaf):
    """
    A duration with duration (in logarithmical form): (-2 ... 8),
    where -2 = \\longa, -1 = \\breve, 0 = 1, 1 = 2, 2 = 4, 3 = 8, 4 = 16, etc,
    dots (number of dots),
    factor (Fraction giving the scaling of the duration).
    """
    def __init__(self, dur, dots=0, factor=1, parent=None):
        super(Duration, self).__init__(parent)
        self.dur = dur # log
        self.dots = dots
        self.factor = fractions.Fraction(factor)

    def ly(self, printer):
        return ly.duration.tostring(self.dur, self.dots, self.factor)


class Chord(Container):
    """
    A chord containing one of more Pitches and optionally one Duration.
    This is a bit of a hack, awaiting real music object support.
    """
    def ly(self, printer):
        pitches = list(self.find_children(Pitch, 1))
        if len(pitches) == 1:
            s = pitches[0].ly(printer)
        else:
            s = "<{0}>".format(' '.join(p.ly(printer) for p in pitches))
        duration = self.find_child(Duration, 1)
        if duration:
            s += duration.ly(printer)
        return s


class Relative(Statement):
    """
    \\relative <pitch> music

    You should add a Pitch (optionally) and another music object,
    e.g. Sim or Seq, etc.
    """
    name = 'relative'


class Transposition(Statement):
    """
    \\transposition <pitch>
    You should add a Pitch.
    """
    name = 'transposition'


class KeySignature(Leaf):
    """
    A key signature expression, like:

    \\key c \\major
    The pitch should be given in the arguments note and alter and is written
    out in the document's language.
    """
    def __init__(self, note=0, alter=0, mode="major", parent=None):
        super(KeySignature, self).__init__(parent)
        self.note = note
        self.alter = fractions.Fraction(alter)
        self.mode = mode

    def ly(self, printer):
        pitch = ly.pitch.pitchWriter(printer.language)(self.note, self.alter)
        return "\\key {0} \\{1}".format(pitch, self.mode)


class TimeSignature(Leaf):
    """
    A time signature, like: \\time 4/4
    """
    def __init__(self, num, beat, parent=None):
        super(TimeSignature, self).__init__(parent)
        self.num = num
        self.beat = beat

    def ly(self, printer):
        return "\\time {0}/{1}".format(self.num, self.beat)


class Partial(Named, Duration):
    """
    \\partial <duration>
    You should add a Duration element
    """
    name = "partial"
    before, after = 1, 1
    
    
class Tempo(Container):
    """
    A tempo setting, like: \\tempo 4 = 100
    May have a child markup or quoted string.
    """
    before, after = 1, 1
    
    def __init__(self, duration, value, parent=None):
        super(Tempo, self).__init__(parent)
        self.duration = duration
        self.value = value
        
    def ly(self, printer):
        result = ['\\tempo']
        if len(self) > 0:
            result.append(super(Tempo, self).ly(printer))
        if self.value:
            result.append("{0}={1}".format(self.duration, self.value))
        return ' '.join(result)
        
        
class Clef(Leaf):
    """
    A clef.
    """
    def __init__(self, clef, parent=None):
        super(Clef, self).__init__(parent)
        self.clef = clef

    def ly(self, printer):
        clef = self.clef if self.clef.isalpha() else '"{0}"'.format(self.clef)
        return "\\clef " + clef


class VoiceSeparator(Leaf):
    """
    A Voice Separator: \\\\
    """
    def ly(self, printer):
        return r'\\'


class Mark(Statement):
    """
    The \\mark command.
    """
    name = 'mark'


class Markup(StatementEnclosed):
    """
    The \\markup command.
    You can add many children, in that case Markup automatically prints
    { and } around them.
    """
    name = 'markup'


class MarkupEnclosed(CommandEnclosed):
    """
    A markup that auto-encloses all its arguments, like 'italic', 'bold'
    etc.  You must supply the name.
    """
    pass


class MarkupCommand(Command):
    """
    A markup command with more or no arguments, that does not auto-enclose
    its arguments. Useful for commands like note-by-number or hspace.

    You must supply the name. Its arguments are its children.
    If one argument can be a markup list, use a Enclosed() construct for that.
    """
    pass



