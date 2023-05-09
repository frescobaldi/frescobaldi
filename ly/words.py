# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2008 - 2015 by Wilbert Berendsen
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
LilyPond reserved words for auto completion and highlighting.
"""

from __future__ import unicode_literals


lilypond_keywords = (
    'accepts',
    'alias',
    'book',
    'bookpart',
    'consists',
    'context',
    'defaultchild',
    'denies',
    'description',
    'etc',
    'header',
    'hide', # since 2.18
    'include',
    'inherit-acceptability',
    'language',
    'layout',
    'midi',
    'name',
    'omit', # since 2.18
    'once',
    'override',
    'paper',
    'remove',
    'revert',
    'score',
    'set',
    'tagGroup', # since 2.20
    'temporary', # since 2.18
    'type',
    'undo', # since 2.18 (not mentioned in the command index)
    'unset',
    'version',
    'with',
)


lilypond_music_commands = (
    'absolute', # since 2.18
    'acciaccatura',
    'accidentalStyle', # since 2.16
    'addChordShape', # since 2.16
    'addInstrumentDefinition',
    'addlyrics',
    'addQuote',
    'after',
    'afterGrace',
    #'afterGraceFraction', # this is a parser variable
    'aikenHeads',
    'aikenHeadsMinor',
    'aikenThinHeads',
    'aikenThinHeadsMinor',
    'allowBreak',
    'allowPageTurn',
    'allowVoltaHook',
    'alterBroken', # since 2.18 (?)
    'alternative',
    'ambitusAfter',
    #'AncientRemoveEmptyStaffContext',
    'appendToTag', # since 2.16
    'applyContext',
    'applyMusic',
    'applyOutput',
    'appoggiatura',
    'arabicStringNumbers', # since 2.20
    'arpeggio',
    'arpeggioArrowDown',
    'arpeggioArrowUp',
    'arpeggioBracket',
    'arpeggioNormal',
    'arpeggioParenthesis',
    'arpeggioParenthesisDashed',
    'ascendens',
    'assertBeamQuant',
    'assertBeamSlope',
    'auctum',
    'aug',
    'augmentum',
    'autoAccidentals',
    'autoBeamOff',
    'autoBeamOn',
    'autoBreaksOff',
    'autoBreaksOn',
    'autoChange',
    'autoLineBreaksOff',
    'autoLineBreaksOn',
    'autoPageBreaksOff',
    'autoPageBreaksOn',
    'balloonGrobText',
    'balloonLengthOff',
    'balloonLengthOn',
    'balloonText',
    'bar',
    'barNumberCheck',
    'bassFigureExtendersOff',
    'bassFigureExtendersOn',
    'bassFigureStaffAlignmentDown',
    'bassFigureStaffAlignmentNeutral',
    'bassFigureStaffAlignmentUp',
    'beamExceptions', # since 2.20
    'bendAfter',
    'bendHold', # since 2.23
    'bendStartLevel',
    'blackTriangleMarkup',
    'bookOutputName',
    'bookOutputSuffix',
    'bracketCloseSymbol',
    'bracketOpenSymbol',
    'break',
    'breathe',
    'breve',
    'cadenzaOff',
    'cadenzaOn',
    'caesura',
    'cavum',
    'change',
    'chordmode',
    #'chordNameSeparator',
    #'chordPrefixSpacer',
    'chordRepeats', # since 2.16
    #'chordRootNamer',
    'chords',
    'clef',
    'cm',
    'compoundMeter', # since 2.16
    #'compressFullBarRests', renamed to compressEmptyMeasures
    'compressEmptyMeasures',
    'compressMMRests', # since 2.23
    'context',
    'cr',
    'cresc',
    'crescHairpin',
    'crescTextCresc',
    'crossStaff', # since 2.16
    'cueClef',  # since 2.16
    'cueClefUnset',  # since 2.16
    'cueDuring',
    'cueDuringWithClef',  # since 2.16
    'dashBar',
    'dashDash',
    'dashDot',
    'dashHat',
    'dashLarger',
    'dashPlus',
    'dashUnderscore',
    'deadNote',  # since 2.16
    'deadNotesOff',
    'deadNotesOn',
    'decr',
    'default',
    'defaultNoteHeads',  # since 2.16
    'defaultTimeSignature',
    'defineBarLine', # since 2.18
    'deminutum',
    'denies',
    'deprecatedcresc',
    'deprecateddim',
    'deprecatedendcresc',
    'deprecatedenddim',
    'descendens',
    'dim',
    'dimHairpin',
    'dimTextDecr',
    'dimTextDecresc',
    'dimTextDim',
    'displayLilyMusic',
    'displayMusic',
    'displayScheme', # since 2.23
    'divisioMaior',
    'divisioMaxima',
    'divisioMinima',
    'dotsDown',
    'dotsNeutral',
    'dotsUp',
    'dropNote', # since 2.23
    'drummode',
    'drumPitchTable',
    'drums',
    'dynamicDown',
    'dynamicNeutral',
    'dynamicUp',
    'easyHeadsOff',
    'easyHeadsOn',
    'enablePolymeter',
    'endcr',
    'endcresc',
    'enddecr',
    'enddim',
    'endincipit',
    'endSkipNCs',
    'endSpanners',
    'episemFinis',
    'episemInitium',
    'escapedBiggerSymbol',
    'escapedExclamationSymbol',
    'escapedParenthesisCloseSymbol',
    'escapedParenthesisOpenSymbol',
    'escapedSmallerSymbol',
    'eventChords', # since 2.23
    'expandEmptyMeasures',
    'expandFullBarRests',
    'f',
    'featherDurations',
    'fermataMarkup',
    'ff',
    'fff',
    'ffff',
    'fffff',
    'figuremode',
    'figures',
    'finalis',
    'fine',
    'finger', # since 2.23
    'fingeringOrientations',
    'fixed', # since 2.23
    'flexa',
    'footnote', # since 2.23
    'fp',
    'frenchChords',
    'fullJazzExceptions',
    'funkHeads',
    'funkHeadsMinor',
    'fz',
    'germanChords',
    'glissando',
    'grace',
    'graceSettings',
    'grobdescriptions', # since 2.23
    'harmonic',
    'harmonicByFret', # since 2.20
    'harmonicByRatio', # since 2.20
    'harmonicNote',
    'harmonicsOff',
    'harmonicsOn',
    'hideNotes',
    'hideSplitTiedTabNotes',
    'hideStaffSwitch',
    'huge',
    'ignatzekExceptionMusic',
    'ignatzekExceptions',
    'iij',
    'IIJ',
    'ij',
    'IJ',
    'improvisationOff',
    'improvisationOn',
    'in',
    'incipit',
    'inclinatum',
    'includePageLayoutFile',
    'indent',
    'inStaffSegno', # since 2.23
    'instrumentSwitch',
    'instrumentTransposition',
    'interscoreline',
    'inversion', # since 2.23
    'invertChords', # since 2.23
    'italianChords',
    'jump',
    'keepWithTag',
    'key',
    'kievanOff',
    'kievanOn',
    'killCues',
    'label',
    'laissezVibrer',
    'languageRestore', # since 2.23
    'languageSaveAndChange', # since 2.23
    'large',
    'ligature',
    'linea',
    'longa',
    'lyricmode',
    'lyrics',
    'lyricsto',
    'magnifyMusic', # since 2.20
    'magnifyStaff', # since 2.23
    'maininput',
    'maj',
    'majorSevenSymbol',
    'makeClusters',
    'makeDefaultStringTuning',
    'mark',
    'markLengthOff', # since 2.18
    'markLengthOn',  # since 2.18
    'markup',
    'markuplines', # deprecated, till 2.14
    'markuplist', # from 2.16
    'markupMap', #since 2.23
    'maxima',
    'medianChordGridStyle',
    'melisma',
    'melismaEnd',
    'mergeDifferentlyDottedOff',
    'mergeDifferentlyDottedOn',
    'mergeDifferentlyHeadedOff',
    'mergeDifferentlyHeadedOn',
    'mf',
    'mm',
    'modalInversion', # since 2.23
    'modalTranspose', # since 2.23
    'mp',
    'musicMap',
    'neumeDemoLayout',
    'new',
    'newSpacingSection',
    'noBeam',
    'noBreak',
    'noPageBreak',
    'noPageTurn',
    'normalsize',
    'notemode',
    'numericTimeSignature',
    'octaveCheck',
    'offset', # since 2.23
    'oldaddlyrics',
    'oneVoice',
    'oriscus',
    'ottava',
    'override',
    'overrideProperty',
    'overrideTimeSignatureSettings',  # since 2.16
    'p',
    'pageBreak',
    'pageTurn',
    'palmMute',  # since 2.16
    'palmMuteOff',
    'palmMuteOn',  # since 2.16
    'parallelMusic',
    'parenthesisCloseSymbol',
    'parenthesisOpenSymbol',
    'parenthesize',
    'partCombine',
    'partCombineApart',
    'partCombineAutomatic',
    'partCombineChords',
    'partCombineDown', # since 2.23
    'partCombineForce',
    'partCombineListener',
    'partCombineSoloI',
    'partCombineSoloII',
    'partCombineUnisono',
    'partCombineUp', # since 2.23
    'partial',
    'partialJazzExceptions',
    'partialJazzMusic',
    'pes',
    'phrasingSlurDashed',
    'phrasingSlurDashPattern',
    'phrasingSlurDotted',
    'phrasingSlurDown',
    'phrasingSlurHalfDashed',
    'phrasingSlurHalfSolid',
    'phrasingSlurNeutral',
    'phrasingSlurSolid',
    'phrasingSlurUp',
    'pipeSymbol',
    'pitchedTrill',
    'pointAndClickOff',
    'pointAndClickOn',
    'pointAndClickTypes',
    'pp',
    'ppp',
    'pppp',
    'ppppp',
    'preBend', # since 2.23
    'preBendHold', # since 2.23
    'predefinedFretboardsOff',
    'predefinedFretboardsOn',
    'propertyOverride', # since 2.23
    'propertyRevert', # since 2.23
    'propertySet', # since 2.23
    'propertyTweak', # since 2.23
    'propertyUnset', # since 2.23
    'pt',
    'pushToTag', # since 2.16
    'quilisma',
    'quoteDuring',
    'raiseNote', # since 2.23
    'reduceChords', # since 2.23
    'relative',
    'RemoveEmptyRhythmicStaffContext',
    'RemoveEmptyStaffContext',
    'removeWithTag',
    'repeat',
    'repeatTie',
    'resetRelativeOctave',
    'responsum',
    'rest',
    'retrograde', # since 2.23
    'revert',
    'revertTimeSignatureSettings', # since 2.23
    'rfz',
    'rightHandFinger',
    'romanStringNumbers', # since 2.20
    'sacredHarpHeads',
    'sacredHarpHeadsMinor',
    'scaleDurations',
    'scoreTweak',
    'section',
    'sectionLabel',
    'segnoMark',
    'semiGermanChords',
    'set',
    'setDefaultDurationToQuarter',
    'settingsFrom', # 2.23
    'sf',
    'sff',
    'sfp',
    'sfz',
    'shape', # since 2.16
    'shiftDurations',
    'shiftOff',
    'shiftOn',
    'shiftOnn',
    'shiftOnnn',
    'showSplitTiedTabNotes',
    'showStaffSwitch',
    'single', # since 2.18
    'skip',
    'skipNC',
    'skipNCs',
    'skipTypesetting',
    'slashedGrace', # since 2.20
    'slurDashed',
    'slurDashPattern',
    'slurDotted',
    'slurDown',
    'slurHalfDashed',
    'slurHalfSolid',
    'slurNeutral',
    'slurSolid',
    'slurUp',
    'small',
    'sostenutoOff',
    'sostenutoOn',
    'southernHarmonyHeads',
    'southernHarmonyHeadsMinor',
    'sp',
    'spacingTweaks',
    'spp',
    'staff-space',
    'staffHighlight',
    'startAcciaccaturaMusic',
    'startAppoggiaturaMusic',
    'startGraceMusic',
    'startGroup',
    'startMeasureCount',
    'startMeasureSpanner',
    'startSlashedGraceMusic',
    'startStaff',
    'startTextSpan',
    'startTrillSpan',
    'stemDown',
    'stemNeutral',
    'stemUp',
    'stopAcciaccaturaMusic',
    'stopAppoggiaturaMusic',
    'stopGraceMusic',
    'stopGroup',
    'stopMeasureCount',
    'stopMeasureSpanner',
    'stopSlashedGraceMusic',
    'stopStaff',
    'stopStaffHighlight',
    'stopTextSpan',
    'stopTrillSpan',
    'storePredefinedDiagram',
    'stringTuning', # since 2.16
    'strokeFingerOrientations',
    'stropha',
    'styledNoteHeads', # since 2.23
    'sustainOff',
    'sustainOn',
    'tabChordRepeats',
    'tabChordRepetition',
    'tabFullNotation',
    'tag',
    'teeny',
    'tempo',
    'tempoWholesPerMinute',
    'textEndMark',
    'textLengthOff',
    'textLengthOn',
    'textMark',
    'textSpannerDown',
    'textSpannerNeutral',
    'textSpannerUp',
    'tieDashed',
    'tieDashPattern',
    'tieDotted',
    'tieDown',
    'tieHalfDashed',
    'tieHalfSolid',
    'tieNeutral',
    'tieSolid',
    'tieUp',
    'tildeSymbol',
    'time',
    'times',
    'timing',
    'tiny',
    'tocItem', # since ?
    'transpose',
    'transposedCueDuring',
    'transposition',
    'treCorde',
    'tuplet', # since 2.18
    'tupletDown',
    'tupletNeutral',
    'tupletSpan', #since 2.23
    'tupletUp',
    'tweak',
    'unaCorda',
    'unfolded', # since 2.23
    'unfoldRepeats',
    'unHideNotes',
    'unit',
    'unset',
    'versus',
    'virga',
    'virgula',
    'voiceFour',
    'voiceFourStyle',
    'voiceNeutralStyle',
    'voiceOne',
    'voiceOneStyle',
    'voices', # since 2.23
    'voiceThree',
    'voiceThreeStyle',
    'voiceTwo',
    'voiceTwoStyle',
    'void', # since 2.23
    'vshape', # since 2.23
    'walkerHeads',
    'walkerHeadsMinor',
    'whiteTriangleMarkup',
    'withMusicProperty',
    'xNote',
    'xNotesOff',
    'xNotesOn',
)


articulations = (
    'accent',
    'espressivo',
    'marcato',
    'portato',
    'staccatissimo',
    'staccato',
    'tenuto',
)


ornaments = (
    'downmordent',
    'downprall',
    'lineprall',
    'mordent',
    'prall',
    'pralldown',
    'prallmordent',
    'prallprall',
    'prallup',
    'reverseturn',
    'trill',
    'turn',
    'upmordent',
    'upprall',
)


fermatas = (
    'fermata',
    'longfermata',
    'shortfermata',
    'verylongfermata',
)


instrument_scripts = (
    'downbow',
    'flageolet',
    'halfopen',
    'lheel',
    'ltoe',
    'open',
    'rheel',
    'rtoe',
    'snappizzicato',
    'stopped',
    'thumb',
    'upbow',
)


repeat_scripts = (
    'coda',
    'segno',
    'varcoda',
)


ancient_scripts = (
    'accentus',
    'circulus',
    'ictus',
    'semicirculus',
    'signumcongruentiae',
)


modes = (
    'aeolian',
    'dorian',
    'ionian',
    'locrian',
    'lydian',
    'major',
    'minor',
    'mixolydian',
    'phrygian',
)


markupcommands_nargs = (
# no arguments
(
    'coda',
    'doubleflat',
    'doublesharp',
    'eyeglasses',
    'fermata',
    'flat',
    'natural',
    'null',
    'segno',
    'semiflat',
    'semisharp',
    'sesquiflat',
    'sesquisharp',
    'sharp',
    'strut',
    'table-of-contents',
    'varcoda',
),
# one argument
(
    'accidental',
    'backslashed-digit',
    'bold',
    'box',
    'bracket',
    'caps',
    'center-align',
    'center-column',
    'char',
    'circle',
    'column',
    'compound-meter',
    'concat',
    'dir-column',
    'discant',
    'draw-dashed-line', # since 2.18
    'draw-dotted-line', # since 2.18
    'draw-hline',
    'draw-line',
    'dynamic',
    'ellipse',
    'fill-line',
    'figured-bass',
    'finger',
    'first-visible',
    'fontCaps',
    'freeBass',
    'fret-diagram',
    'fret-diagram-terse',
    'fret-diagram-verbose',
    'fromproperty',
    'harp-pedal',
    'hbracket',
    'hspace',
    'huge',
    'italic',
    'justify',
    'justify-field',
    'justify-line', #since 2.20
    'justify-string',
    'large',
    'larger',
    'left-align',
    'left-brace',
    'left-column',
    'line',
    'lookup',
    'markalphabet',
    'markletter',
    'medium',
    'multi-measure-rest-by-number',
    'musicglyph',
    'normalsize',
    'normal-size-sub',
    'normal-size-super',
    'normal-text',
    'number',
    'oval', # since 2.18
    'overlay', # since 2.20
    'overtie', # since 2.20
    'polygon',
    'postscript',
    'property-recursive',
    'rest',
    'right-align',
    'right-brace',
    'right-column',
    'roman',
    'rounded-box',
    'rhythm',
    'sans',
    'score',
    'score-lines',
    'simple',
    'slashed-digit',
    'small',
    'smallCaps',
    'smaller',
    'stencil',
    'string-lines',
    'sub',
    'super',
    'teeny',
    'text',
    'tie', # since 2.20
    'tied-lyric',
    'tiny',
    'transparent',
    'triangle',
    'typewriter',
    'underline',
    'undertie', # since 2.20
    'upright',
    'vcenter',
    'verbatim-file',
    'vspace',
    'whiteout',
    'with-true-dimensions',
    'wordwrap',
    'wordwrap-field',
    'wordwrap-string',
),
# two arguments
(
    'abs-fontsize',
    'auto-footnote', # since 2.16
    'combine',
    'customTabClef',
    'fontsize',
    'footnote',
    'fraction',
    'halign',
    'hcenter-in',
    'if',
    'lower',
    'magnify',
    'note',
    'on-the-fly',
    'override',
    'pad-around',
    'pad-markup',
    'pad-x',
    'page-link',
    'path',     # added in LP 2.13.31
    'raise',
    'replace',
    'rest-by-number',
    'rotate',
    'scale',
    'translate',
    'translate-scaled',
    'unless',
    'with-color',
    'with-dimensions-from', # since 2.20
    'with-link',
    'with-outline',
    'with-string-transformer',
    'with-true-dimension',
    'with-url',
    'woodwind-diagram',
),
# three arguments
(
    'arrow-head',
    'beam',
    'draw-circle',
    'draw-squiggle-line', # since 2.20
    'epsfile',
    'filled-box',
    'general-align',
    'note-by-number',
    'pad-to-box',
    'page-ref',
    'with-dimension',
    'with-dimension-from',
    'with-dimensions',
),
# four arguments
(
    'pattern',
    'put-adjacent',
),
# five arguments,
(
    'align-on-other',
    'fill-with-pattern',
),
)


markupcommands = sum(markupcommands_nargs, ())


markuplistcommands = (
    'column-lines',
    'justified-lines',
    'override-lines',
    'wordwrap-internal',
    'wordwrap-lines',
    'wordwrap-string-internal',
)


contexts = (
    'ChoirStaff',
    'ChordGrid',
    'ChordGridScore',
    'ChordNames',
    'CueVoice',
    'Devnull',
    'DrumStaff',
    'DrumVoice',
    'Dynamics',
    'FiguredBass',
    'FretBoards',
    'Global',
    'GrandStaff',
    'GregorianTranscriptionLyrics',
    'GregorianTranscriptionStaff',
    'GregorianTranscriptionVoice',
    'InternalGregorianStaff',
    'KievanStaff', # since 2.16
    'KievanVoice', # since 2.16
    'Lyrics',
    'MensuralStaff',
    'MensuralVoice',
    'NoteNames',
    'NullVoice',     # since 2.18
    'OneStaff',
    'PetrucciStaff', # since 2.16
    'PetrucciVoice', # since 2.16
    'PianoStaff',
    'RhythmicStaff',
    'Score',
    'Staff',
    'StaffGroup',
    'StandaloneRhythmScore',
    'StandaloneRhythmStaff',
    'StandaloneRhythmVoice',
    'TabStaff',
    'TabVoice',
    'Timing',
    'VaticanaLyrics',
    'VaticanaStaff',
    'VaticanaVoice',
    'Voice',
)


midi_instruments = (
    # (1-8 piano)
    'acoustic grand',
    'bright acoustic',
    'electric grand',
    'honky-tonk',
    'electric piano 1',
    'electric piano 2',
    'harpsichord',
    'clav',
    # (9-16 chrom percussion)
    'celesta',
    'glockenspiel',
    'music box',
    'vibraphone',
    'marimba',
    'xylophone',
    'tubular bells',
    'dulcimer',
    # (17-24 organ)
    'drawbar organ',
    'percussive organ',
    'rock organ',
    'church organ',
    'reed organ',
    'accordion',
    'harmonica',
    'concertina',
    # (25-32 guitar)
    'acoustic guitar (nylon)',
    'acoustic guitar (steel)',
    'electric guitar (jazz)',
    'electric guitar (clean)',
    'electric guitar (muted)',
    'overdriven guitar',
    'distorted guitar',
    'guitar harmonics',
    # (33-40 bass)
    'acoustic bass',
    'electric bass (finger)',
    'electric bass (pick)',
    'fretless bass',
    'slap bass 1',
    'slap bass 2',
    'synth bass 1',
    'synth bass 2',
    # (41-48 strings)
    'violin',
    'viola',
    'cello',
    'contrabass',
    'tremolo strings',
    'pizzicato strings',
    'orchestral harp', # till LilyPond 2.12 was this erroneously called: 'orchestral strings'
    'timpani',
    # (49-56 ensemble)
    'string ensemble 1',
    'string ensemble 2',
    'synthstrings 1',
    'synthstrings 2',
    'choir aahs',
    'voice oohs',
    'synth voice',
    'orchestra hit',
    # (57-64 brass)
    'trumpet',
    'trombone',
    'tuba',
    'muted trumpet',
    'french horn',
    'brass section',
    'synthbrass 1',
    'synthbrass 2',
    # (65-72 reed)
    'soprano sax',
    'alto sax',
    'tenor sax',
    'baritone sax',
    'oboe',
    'english horn',
    'bassoon',
    'clarinet',
    # (73-80 pipe)
    'piccolo',
    'flute',
    'recorder',
    'pan flute',
    'blown bottle',
    'shakuhachi',
    'whistle',
    'ocarina',
    # (81-88 synth lead)
    'lead 1 (square)',
    'lead 2 (sawtooth)',
    'lead 3 (calliope)',
    'lead 4 (chiff)',
    'lead 5 (charang)',
    'lead 6 (voice)',
    'lead 7 (fifths)',
    'lead 8 (bass+lead)',
    # (89-96 synth pad)
    'pad 1 (new age)',
    'pad 2 (warm)',
    'pad 3 (polysynth)',
    'pad 4 (choir)',
    'pad 5 (bowed)',
    'pad 6 (metallic)',
    'pad 7 (halo)',
    'pad 8 (sweep)',
    # (97-104 synth effects)
    'fx 1 (rain)',
    'fx 2 (soundtrack)',
    'fx 3 (crystal)',
    'fx 4 (atmosphere)',
    'fx 5 (brightness)',
    'fx 6 (goblins)',
    'fx 7 (echoes)',
    'fx 8 (sci-fi)',
    # (105-112 ethnic)
    'sitar',
    'banjo',
    'shamisen',
    'koto',
    'kalimba',
    'bagpipe',
    'fiddle',
    'shanai',
    # (113-120 percussive)
    'tinkle bell',
    'agogo',
    'steel drums',
    'woodblock',
    'taiko drum',
    'melodic tom',
    'synth drum',
    'reverse cymbal',
    # (121-128 sound effects)
    'guitar fret noise',
    'breath noise',
    'seashore',
    'bird tweet',
    'telephone ring',
    'helicopter',
    'applause',
    'gunshot',
    # (channel 10 drum-kits - subtract 32768 to get program no.)
    'standard kit',
    'standard drums',
    'drums',
    'room kit',
    'room drums',
    'power kit',
    'power drums',
    'rock drums',
    'electronic kit',
    'electronic drums',
    'tr-808 kit',
    'tr-808 drums',
    'jazz kit',
    'jazz drums',
    'brush kit',
    'brush drums',
    'orchestra kit',
    'orchestra drums',
    'classical drums',
    'sfx kit',
    'sfx drums',
    'mt-32 kit',
    'mt-32 drums',
    'cm-64 kit',
    'cm-64 drums',
)

# Follow the order of lilypond sources in ly/string-tunings-init.ly
string_tunings = (
    'guitar-tuning',
    'guitar-seven-string-tuning',
    'guitar-drop-d-tuning',
    'guitar-drop-c-tuning',
    'guitar-open-g-tuning',
    'guitar-open-d-tuning',
    'guitar-dadgad-tuning',
    'guitar-lute-tuning',
    'guitar-asus4-tuning',
    'bass-tuning',
    'bass-four-string-tuning',
    'bass-drop-d-tuning',
    'bass-five-string-tuning',
    'bass-six-string-tuning',
    'mandolin-tuning',
    'banjo-open-g-tuning',
    'banjo-c-tuning',
    'banjo-modal-tuning',
    'banjo-open-d-tuning',
    'banjo-open-dm-tuning',
    'banjo-double-c-tuning',
    'banjo-double-d-tuning',
    'ukulele-tuning',
    'ukulele-d-tuning',
    'tenor-ukulele-tuning',
    'baritone-ukulele-tuning',
    'violin-tuning',
    'viola-tuning',
    'cello-tuning',
    'double-bass-tuning',
)

#scheme_functions = (
#    'set-accidental-style',
#    'set-global-staff-size',
#    'set-octavation',
#    'set-paper-size',
#    'define-public',
#    'define-music-function',
#    'define-markup-command',
#    'empty-stencil',
#    'markup',
#    'number?',
#    'string?',
#    'pair?',
#    'ly:duration?',
#    'ly:grob?',
#    'ly:make-moment',
#    'ly:make-pitch',
#    'ly:music?',
#    'ly:moment?',
#    'ly:format',
#    'markup?',
#    'interpret-markup',
#    'make-line-markup',
#    'make-center-markup',
#    'make-column-markup',
#    'make-musicglyph-markup',
#    'color?',
#    'rgb-color',
#    'x11-color',
#)


scheme_values = (
    'UP',
    'DOWN',
    'LEFT',
    'RIGHT',
    'CENTER',
    'minimum-distance',
    'basic-distance',
    'padding',
    'stretchability',
)


headervariables = (
    'arranger',
    'breakbefore',
    'composer',
    'copyright',
    'date',
    'dedication',
    'enteredby',
    'footer',
    'instrument',
    'lastupdated',
    'maintainer',
    'maintainerEmail',
    'maintainerWeb',
    'meter',
    'moreInfo',
    'mutopiacomposer',
    'mutopiainstrument',
    'mutopiaopus',
    'mutopiapoet',
    'mutopiatitle',
    'opus',
    'piece',
    'poet',
    'source',
    'style',
    'subsubtitle',
    'subtitle',
    'tagline',
    'texidoc',
    'title',
)


papervariables = (
    # fixed vertical
    'paper-height',
    'top-margin',
    'bottom-margin',
    'ragged-bottom',
    'ragged-last-bottom',

    # horizontal
    'paper-width',
    'line-width',
    'left-margin',
    'right-margin',
    'check-consistency',
    'ragged-right',
    'ragged-last',
    'two-sided',
    'inner-margin',
    'outer-margin',
    'binding-offset',
    'horizontal-shift',
    'indent',
    'short-indent',

    # flex vertical
    'markup-system-spacing', # the distance between a (title or top-level) markup and the system that follows it.
    'score-markup-spacing',  # the distance between the last system of a score and the (title or top-level) markup that follows it.
    'score-system-spacing',  # the distance between the last system of a score and the first system of the score that follows it, when no (title or top-level) markup exists between them.
    'system-system-spacing', # the distance between two systems in the same score.
    'markup-markup-spacing', # the distance between two (title or top-level) markups.
    'last-bottom-spacing',   # the distance from the last system or top-level markup on a page to the bottom of the printable area (i.e. the top of the bottom margin).
    'top-system-spacing',    # the distance from the top of the printable area (i.e. the bottom of the top margin) to the first system on a page, when there is no (title or top-level) markup between the two.
    'top-markup-spacing',    # the distance from the top of the printable area (i.e. the bottom of the top margin) to the first (title or top-level) markup on a page, when there is no system between the two.

    # line breaking
    'max-systems-per-page',
    'min-systems-per-page',
    'system-count',
    'systems-per-page',

    # page breaking
    'blank-after-score-page-force',  # The penalty for having a blank page after the end of one score and before the next. By default, this is smaller than blank-page-force, so that we prefer blank pages after scores to blank pages within a score.
    'blank-last-page-force',         # The penalty for ending the score on an odd-numbered page.
    'blank-page-force',              # The penalty for having a blank page in the middle of a score. This is not used by ly:optimal-breaking since it will never consider blank pages in the middle of a score.
    'page-breaking',                 # The page-breaking algorithm to use. Choices are ly:minimal-breaking, ly:page-turn-breaking, and ly:optimal-breaking.
    'page-breaking-system-system-spacing', # Tricks the page breaker into thinking that system-system-spacing is set to something different than it really is. For example, if page-breaking-system-system-spacing #'padding is set to something substantially larger than system-system-spacing #'padding, then the page-breaker will put fewer systems on each page. Default: unset.
    'page-count',                    # The number of pages to be used for a score, unset by default.

    # page numbering
    'auto-first-page-number',
    'first-page-number',
    'print-first-page-number',
    'print-page-number',

    # misc
    'footnote-separator-markup',
    'page-spacing-weight',
    'print-all-headers',
    'system-separator-markup',

    # debugging
    'annotate-spacing',

    # different markups
    'bookTitleMarkup',
    'evenFooterMarkup',
    'evenHeaderMarkup',
    'oddFooterMarkup',
    'oddHeaderMarkup',
    'scoreTitleMarkup',
    'tocItemMarkup',
    'tocTitleMarkup',

    # fonts
    'fonts',

    # undocumented?
    #'blank-after-score-page-force',
    #'force-assignment',
    #'input-encoding',
    #'output-scale',
)


layoutvariables = (
    'indent',
    'line-width',
    'ragged-last',
    'ragged-right',
    'short-indent',
    'system-count',
)


midivariables = (
)


repeat_types = (
    'percent',
    'segno',
    'tremolo',
    'unfold',
    'volta',
)


accidentalstyles = (
    'choral', # since 2.20
    'choral-cautionary', # since 2.20
    'default',
    'dodecaphonic',
    'forget',
    'modern',
    'modern-cautionary',
    'modern-voice',
    'modern-voice-cautionary',
    'neo-modern',
    'neo-modern-cautionary',
    'neo-modern-voice',
    'neo-modern-voice-cautionary',
    'no-reset',
    'piano',
    'piano-cautionary',
    'teaching',
    'voice',
)


clefs_plain = (
    'alto',
    'altovarC',
    'baritone',
    'baritonevarC',
    'baritonevarF',
    'bass',
    'blackmensural-c1',
    'blackmensural-c2',
    'blackmensural-c3',
    'blackmensural-c4',
    'blackmensural-c5',
    'C',
    'F',
    'french',
    'G',
    'GG',               # since 2.19
    'G2',
    'hufnagel-do-fa',
    'hufnagel-do1',
    'hufnagel-do2',
    'hufnagel-do3',
    'hufnagel-fa1',
    'hufnagel-fa2',
    'kievan-do',
    'medicaea-do1',
    'medicaea-do2',
    'medicaea-do3',
    'medicaea-fa1',
    'medicaea-fa2',
    'mensural-c1',
    'mensural-c2',
    'mensural-c3',
    'mensural-c4',
    'mensural-c5',
    'mensural-f',
    'mensural-g',
    'mezzosoprano',
    'moderntab',
    'neomensural-c1',
    'neomensural-c2',
    'neomensural-c3',
    'neomensural-c4',
    'neomensural-c5',
    'percussion',
    'petrucci-c1',
    'petrucci-c2',
    'petrucci-c3',
    'petrucci-c4',
    'petrucci-c5',
    'petrucci-f',
    'petrucci-f2',
    'petrucci-f3',
    'petrucci-f4',
    'petrucci-f5',
    'petrucci-g',
    'petrucci-g1',
    'petrucci-g2',
    'soprano',
    'subbass',
    'tab',
    'tenor',
    'tenorG',           # since 2.19
    'tenorvarC',
    'treble',
    'varbaritone',
    'varC',             # since 2.19
    'varpercussion',    # since 2.19
    'vaticana-do1',
    'vaticana-do2',
    'vaticana-do3',
    'vaticana-fa1',
    'vaticana-fa2',
    'violin',
)


clefs = clefs_plain + (
    'bass_8',
    'treble_8',
)


break_visibility = (
    'all-invisible',
    'all-visible',
    'begin-of-line-invisible',
    'begin-of-line-visible',
    'center-invisible',
    'end-of-line-invisible',
    'end-of-line-visible',
)


mark_formatters = (
    'format-mark-alphabet',
    'format-mark-barnumbers',
    'format-mark-box-alphabet',
    'format-mark-box-barnumbers',
    'format-mark-box-letters',
    'format-mark-box-numbers',
    'format-mark-circle-alphabet',
    'format-mark-circle-barnumbers',
    'format-mark-circle-letters',
    'format-mark-circle-numbers',
    'format-mark-letters',
    'format-mark-numbers',
)


