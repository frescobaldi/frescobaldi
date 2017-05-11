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
Builds the LilyPond score from the settings in the Score Wizard.
"""


import collections
import fractions
import re

import ly.dom
import po.mofile
import lasptyqu

from . import parts


class PartNode(object):
    """Represents an item with sub-items in the parts tree.

    Sub-items of this items are are split out in two lists: the 'parts' and
    'groups' attributes.

    Parts ('parts' attribute) are vertically stacked (instrumental parts or
    staff groups). Groups ('groups' attribute) are horizontally added (score,
    book, bookpart).

    The Part (containing the widgets) is in the 'part' attribute.

    """
    def __init__(self, item):
        """item is a PartItem (QTreeWidgetItem)."""
        self.part = getattr(item, 'part', None)
        self.groups = []
        self.parts = []
        for i in range(item.childCount()):
            node = PartNode(item.child(i))
            if isinstance(node.part, parts._base.Group):
                self.groups.append(node)
            else:
                self.parts.append(node)


class PartData(object):
    r"""Represents what a Part wants to add to the LilyPond score.

    A Part may append to the following instance attributes (which are lists):

    includes:           (string) filename to be included
    codeblocks:         (ly.dom.LyNode) global blocks of code a part depends on
    assignments:        (ly.dom.Assignment) assignment of an expression to a
                        variable, most times the music stub for a part
    nodes:              (ly.dom.LyNode) the nodes a part adds to the parent \score
    afterblocks:        (ly.dom.LyNode) other blocks, appended ad the end

    The num instance attribute is set to 0 by default but can be increased by
    the Builder, when there are more parts of the exact same type in the same
    score.

    This is used by the builder afterwards to adjust identifiers and instrument
    names to this.

    """
    def __init__(self, part, parent=None):
        """part is a parts._base.Part instance, parent may be another PartData."""
        if parent:
            parent.children.append(self)
        self.isChild = bool(parent)
        self._name = part.__class__.__name__
        self.children = []
        self.num = 0
        self.includes = []
        self.codeblocks = []
        self.assignments = []
        self.nodes = []
        self.afterblocks = []

    def name(self):
        """Returns a name for this part data.

        The name consists of the class name of the part with the value of the num
        attribute appended as a roman number.

        """
        if self.num:
            return self._name + ly.util.int2roman(self.num)
        return self._name

    def assign(self, name=None):
        """Creates a ly.dom.Assignment.

        name is a string name, if not given the class name is used with the
        first letter lowered.

        A ly.dom.Reference is used as the name for the Assignment.
        The assignment is appended to our assignments and returned.

        The Reference is in the name attribute of the assignment.

        """
        a = ly.dom.Assignment(ly.dom.Reference(name or ly.util.mkid(self.name())))
        self.assignments.append(a)
        return a

    def assignMusic(self, name=None, octave=0, transposition=None):
        """Creates a ly.dom.Assignment with a \\relative music stub."""
        a = self.assign(name)
        stub = ly.dom.Relative(a)
        ly.dom.Pitch(octave, 0, 0, stub)
        s = ly.dom.Seq(stub)
        ly.dom.Identifier(self.globalName, s).after = 1
        if transposition is not None:
            toct, tnote, talter = transposition
            ly.dom.Pitch(toct, tnote, fractions.Fraction(talter, 2), ly.dom.Transposition(s))
        ly.dom.LineComment(_("Music follows here."), s)
        ly.dom.BlankLine(s)
        return a


class BlockData(object):
    """Represents the building blocks of a global section of a ly.dom.Document."""
    def __init__(self):
        self.assignments = ly.dom.Block()
        self.scores = ly.dom.Block()
        self.backmatter = ly.dom.Block()


class Builder(object):
    """Builds the LilyPond score from all user input in the score wizard.

    Reads settings and other input from the dialog on construction.
    Does not need the dialog after that.

    """
    def __init__(self, dialog):
        """Initializes ourselves from all user settings in the dialog."""
        self._includeFiles = []
        self.globalUsed = False

        scoreProperties = dialog.settings.widget().scoreProperties
        generalPreferences = dialog.settings.widget().generalPreferences
        lilyPondPreferences = dialog.settings.widget().lilyPondPreferences
        instrumentNames = dialog.settings.widget().instrumentNames

        # attributes the Part and Container types may read and we need later as well
        self.header = list(dialog.header.widget().headers())
        self.headerDict = dict(self.header)
        self.lyVersionString = lilyPondPreferences.version.currentText().strip()
        self.lyVersion = tuple(map(int, re.findall('\\d+', self.lyVersionString)))
        self.midi = generalPreferences.midi.isChecked()
        self.pitchLanguage = dialog.pitchLanguage()
        self.suppressTagLine = generalPreferences.tagl.isChecked()
        self.removeBarNumbers = generalPreferences.barnum.isChecked()
        self.smartNeutralDirection = generalPreferences.neutdir.isChecked()
        self.showMetronomeMark = generalPreferences.metro.isChecked()
        self.paperSize = generalPreferences.getPaperSize()
        self.paperLandscape = generalPreferences.paperOrientationGroup.checkedId() == 1
        self.paperRotated = generalPreferences.paperOrientationGroup.checkedId() == 2
        self.showInstrumentNames = instrumentNames.isChecked()
        names = ['long', 'short', None]
        self.firstInstrumentName = names[instrumentNames.firstSystem.currentIndex()]
        self.otherInstrumentName = names[instrumentNames.otherSystems.currentIndex()]

        # translator for instrument names
        self._ = _
        if instrumentNames.isChecked():
            lang = instrumentNames.getLanguage()
            if lang == 'C':
                self._ = po.translator(None)
            elif lang:
                mofile = po.find(lang)
                if mofile:
                    self._ = po.translator(po.mofile.MoFile(mofile))

        # global score preferences
        self.scoreProperties = scoreProperties
        self.globalSection = scoreProperties.globalSection(self)

        # printer that converts the ly.dom tree to text
        p = self._printer = ly.dom.Printer()
        p.indentString = "  " # will be re-indented anyway
        p.typographicalQuotes = generalPreferences.typq.isChecked()
        quotes = lasptyqu.preferred()
        p.primary_quote_left = quotes.primary.left
        p.primary_quote_right = quotes.primary.right
        p.secondary_quote_left = quotes.secondary.left
        p.secondary_quote_right = quotes.secondary.right
        if self.pitchLanguage:
            p.language = self.pitchLanguage

        # get the parts
        globalGroup = PartNode(dialog.parts.widget().rootPartItem())

        # move parts down the tree to subgroups that have no parts
        assignparts(globalGroup)

        # now prepare the different blocks
        self.usePrefix = needsPrefix(globalGroup)
        self.currentScore = 0

        # make a part of the document (assignments, scores, backmatter) for
        # every group (book, bookpart or score) in the global group
        if globalGroup.parts:
            groups = [globalGroup]
        else:
            groups = globalGroup.groups

        self.blocks = []
        for group in groups:
            block = BlockData()
            self.makeBlock(group, block.scores, block)
            self.blocks.append(block)

    def makeBlock(self, group, node, block):
        """Recursively populates the Block with data from the group.

        The group can contain parts and/or subgroups.
        ly.dom.LyNodes representing the LilyPond document are added to the node.

        """
        if group.part:
            node = group.part.makeNode(node)
        if group.parts:
            # prefix for this block, used if necessary
            self.currentScore += 1
            prefix = 'score' + ly.util.int2letter(self.currentScore)

            # is this a score and has it its own score properties?
            globalName = 'global'
            scoreProperties = self.scoreProperties
            if isinstance(group.part, parts.containers.Score):
                globalSection = group.part.globalSection(self)
                if globalSection:
                    scoreProperties = group.part
                    globalName = prefix + 'Global'
                    a = ly.dom.Assignment(globalName, block.assignments)
                    a.append(globalSection)
                    ly.dom.BlankLine(block.assignments)
            if globalName == 'global':
                self.globalUsed = True

            # add parts here, always in \score { }
            score = node if isinstance(node,ly.dom.Score) else ly.dom.Score(node)
            ly.dom.Layout(score)
            if self.midi:
                midi = ly.dom.Midi(score)
                # set MIDI tempo if necessary
                if not self.showMetronomeMark:
                    if self.lyVersion >= (2, 16, 0):
                        scoreProperties.lySimpleMidiTempo(midi)
                        midi[0].after = 1
                    else:
                        scoreProperties.lyMidiTempo(ly.dom.Context('Score', midi))
            music = ly.dom.Simr()
            score.insert(0, music)

            # a PartData subclass "knowing" the globalName and scoreProperties
            class _PartData(PartData): pass
            _PartData.globalName = globalName
            _PartData.scoreProperties = scoreProperties

            # make the parts
            partData = self.makeParts(group.parts, _PartData)

            # record the include files a part wants to add
            for p in partData:
                for i in p.includes:
                    if i not in self._includeFiles:
                        self._includeFiles.append(i)

            # collect all 'prefixable' assignments for this group
            assignments = []
            for p in partData:
                assignments.extend(p.assignments)

            # add the assignments to the block
            for p in partData:
                for a in p.assignments:
                    block.assignments.append(a)
                    ly.dom.BlankLine(block.assignments)
                block.backmatter.extend(p.afterblocks)

            # make part assignments if there is more than one part that has assignments
            if sum(1 for p in partData if p.assignments) > 1:
                def make(part, music):
                    if part.assignments:
                        a = ly.dom.Assignment(ly.dom.Reference(ly.util.mkid(part.name() + "Part")))
                        ly.dom.Simr(a).extend(part.nodes)
                        ly.dom.Identifier(a.name, music).after = 1
                        block.assignments.append(a)
                        ly.dom.BlankLine(block.assignments)
                        assignments.append(a)
                    else:
                        music.extend(part.nodes)
            else:
                def make(part, music):
                    music.extend(part.nodes)

            def makeRecursive(parts, music):
                for part in parts:
                    make(part, music)
                    if part.children:
                        makeRecursive(part.children, part.music)

            parents = [p for p in partData if not p.isChild]
            makeRecursive(parents, music)

            # add the prefix to the assignments if necessary
            if self.usePrefix:
                for a in assignments:
                    a.name.name = ly.util.mkid(prefix, a.name.name)

        for g in group.groups:
            self.makeBlock(g, node, block)

    def makeParts(self, parts, partDataClass):
        """Lets the parts build the music stubs and assignments.

        parts is a list of PartNode instances.
        partDataClass is a subclass or PartData containing some attributes:
            - globalName is either 'global' (for the global time/key signature
              section) or something like 'scoreAGlobal' (when a score has its
              own properties).
            - scoreProperties is the ScoreProperties instance currently in effect
              (the global one or a particular Score part's one).

        Returns the list of PartData object for the parts.

        """
        # number instances of the same type (Choir I and Choir II, etc.)
        data = {}
        types = collections.defaultdict(list)
        def _search(parts, parent=None):
            for group in parts:
                pd = data[group] = partDataClass(group.part, parent)
                types[pd.name()].append(group)
                _search(group.parts, pd)
        _search(parts)
        for t in types.values():
            if len(t) > 1:
                for num, group in enumerate(t, 1):
                    data[group].num = num

        # now build all the parts
        for group in allparts(parts):
            group.part.build(data[group], self)

        # check for name collisions in assignment identifiers
        # add the part class name and a roman number if necessary
        refs = collections.defaultdict(list)
        for group in allparts(parts):
            for a in data[group].assignments:
                ref = a.name
                name = ref.name
                refs[name].append((ref, group))
        for reflist in refs.values():
            if len(reflist) > 1:
                for ref, group in reflist:
                    # append the class name and number
                    ref.name = ly.util.mkid(ref.name, data[group].name())

        # return all PartData instances
        return [data[group] for group in allparts(parts)]

    def text(self, doc=None):
        """Return LilyPond formatted output. """
        return self.printer().indent(doc or self.document())

    def printer(self):
        """Returns a ly.dom.Printer, that converts the ly.dom structure to LilyPond text. """
        return self._printer

    def document(self):
        """Creates and returns a ly.dom tree representing the full LilyPond document."""
        doc = ly.dom.Document()

        # version
        ly.dom.Version(self.lyVersionString, doc)

        # language
        if self.pitchLanguage:
            if self.lyVersion >= (2, 13, 38):
                ly.dom.Line('\\language "{0}"'.format(self.pitchLanguage), doc)
            else:
                ly.dom.Include("{0}.ly".format(self.pitchLanguage), doc)
        ly.dom.BlankLine(doc)

        # other include files
        if self._includeFiles:
            for filename in self._includeFiles:
                ly.dom.Include(filename, doc)
            ly.dom.BlankLine(doc)

        # general header
        h = ly.dom.Header()
        for name, value in self.header:
            h[name] = value
        if 'tagline' not in h and self.suppressTagLine:
            ly.dom.Comment(_("Remove default LilyPond tagline"), h)
            h['tagline'] = ly.dom.Scheme('#f')
        if len(h):
            doc.append(h)
            ly.dom.BlankLine(doc)

        # paper size
        if self.paperSize:
            ly.dom.Scheme(
                '(set-paper-size "{0}{1}"{2})'.format(
                    self.paperSize,
                    "landscape" if self.paperLandscape else "",
                " 'landscape" if self.paperRotated else ""),
                ly.dom.Paper(doc)
            ).after = 1
            ly.dom.BlankLine(doc)

        layout = ly.dom.Layout()

        # remove bar numbers
        if self.removeBarNumbers:
            ly.dom.Line('\\remove "Bar_number_engraver"',
                ly.dom.Context('Score', layout))

        # smart neutral direction
        if self.smartNeutralDirection:
            ctxt_voice = ly.dom.Context('Voice', layout)
            ly.dom.Line('\\consists "Melody_engraver"', ctxt_voice)
            ly.dom.Line("\\override Stem #'neutral-direction = #'()", ctxt_voice)

        if len(layout):
            doc.append(layout)
            ly.dom.BlankLine(doc)

        # global section
        if self.globalUsed:
            a = ly.dom.Assignment('global')
            a.append(self.globalSection)
            doc.append(a)
            ly.dom.BlankLine(doc)

        # add the main scores
        for block in self.blocks:
            doc.append(block.assignments)
            doc.append(block.scores)
            ly.dom.BlankLine(doc)
            if len(block.backmatter):
                doc.append(block.backmatter)
                ly.dom.BlankLine(doc)
        return doc

    def setMidiInstrument(self, node, midiInstrument):
        """Sets the MIDI instrument for the node, if the user wants MIDI output."""
        if self.midi:
            node.getWith()['midiInstrument'] = midiInstrument

    def setInstrumentNames(self, staff, longName, shortName):
        """Sets the instrument names to the staff (or group).

        longName and shortName may either be a string or a ly.dom.LyNode object (markup)
        The settings in the score wizard are honored.

        """
        if self.showInstrumentNames:
            staff.addInstrumentNameEngraverIfNecessary()
            w = staff.getWith()
            first = longName if self.firstInstrumentName == 'long' else shortName
            w['instrumentName'] = first
            if self.otherInstrumentName:
                other = longName if self.otherInstrumentName == 'long' else shortName
                # If these are markup objects, copy them otherwise the assignment
                # to shortInstrumentName takes it away from the instrumentName.
                if other is first and isinstance(first, ly.dom.LyNode):
                    other = other.copy()
                w['shortInstrumentName'] = other

    def instrumentName(self, function, num=0):
        """Returns an instrument name.

        The name is constructed by calling the 'function' with our translator as
        argument, and appending the number 'num' in roman literals, if num > 0.

        """
        name = function(self._)
        if num:
            name += ' ' + ly.util.int2roman(num)
        return name

    def setInstrumentNamesFromPart(self, node, part, data):
        """Sets the long and short instrument names for the node.

        Calls part.title(translator) and part.short(translator) to get the
        names, appends roman literals if data.num > 0, and sets them on the node.

        """
        longName = self.instrumentName(part.title, data.num)
        shortName = self.instrumentName(part.short, data.num)
        self.setInstrumentNames(node, longName, shortName)


def assignparts(group):
    """Moves the parts to sub-groups that contain no parts.

    If at least one subgroup uses the parts, the parent's parts are removed.
    This way a user can specify some parts and then multiple scores, and they will all
    use the same parts again.

    """
    partsOfParentUsed = False
    for g in group.groups:
        if not g.parts:
            g.parts = group.parts
            partsOfParentUsed = True
        assignparts(g)
    if partsOfParentUsed:
        group.parts = []


def itergroups(group):
    """Iterates over the group and its subgroups as an event list.

    When a group is yielded, it means the group starts.
    When None is yielded, it means that the last started groups ends.

    """
    yield group
    for g in group.groups:
        for i in itergroups(g):
            yield i
    yield None # end a group


def descendants(group):
    """Iterates over the descendants of a group (including the group itself).

    First the group, then its children, then the grandchildren, etc.

    """
    def _descendants(group):
        children = group.groups
        while children:
            new = []
            for g in children:
                yield g
                new.extend(g.groups)
            children = new
    yield group
    for g in _descendants(group):
        yield g


def needsPrefix(globalGroup):
    """Returns True if there are multiple scores in group with shared part types.

    This means the music assignments will need a prefix (e.g. scoreAsoprano,
    scoreBsoprano, etc.)

    """
    counter = collections.Counter()
    for group in itergroups(globalGroup):
        if group:
            counter.update(type(g.part) for g in group.parts)
    return bool(counter) and max(counter.values()) > 1


def allparts(parts):
    """Yields all the parts and child parts."""
    for group in parts:
        yield group
        for group in allparts(group.parts):
            yield group

