# The 'pytest-qt' pytest plugin is required.

import pytest

from PyQt6.QtCore import Qt, QKeyCombination
from PyQt6.QtGui import QKeySequence

import i18n
i18n.install('en') # global function _() is required by the widget module

from widgets.keysequencewidget import KeySequenceWidget

@pytest.fixture
def widget(qtbot):
    widget = KeySequenceWidget()
    widget.show()
    qtbot.addWidget(widget)
    return widget


def test_initial_state(widget):
    assert widget.shortcut().isEmpty()
    assert not widget.button.isRecording()
    assert widget.button.text() == ''

def test_set_shortcut(widget):
    widget.setShortcut(QKeySequence(QKeyCombination(Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_A)))
    assert not widget.shortcut().isEmpty()
    assert widget.button.text() == 'Ctrl+A'

def test_start_recording(widget, qtbot):
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)
    assert widget.button.isRecording()

def test_query_stops_recording(widget, qtbot):
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)
    assert widget.button.isRecording()

    # caveat: accessing shortcut() is not an idempotent query,
    #   it modifies the widget's state
    widget.shortcut()
    assert not widget.button.isRecording()

def test_simple_sequence(widget, qtbot):
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)
    assert widget.button.text() == 'Input ...'

    qtbot.keyClick(widget.button, 'A', modifier=Qt.KeyboardModifier.ControlModifier)
    assert widget.button.text() == 'Ctrl+A ...'
    assert widget.button.isRecording()
    assert not widget.shortcut().isEmpty()
    assert widget.shortcut() == QKeySequence(QKeyCombination(Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_A))

def test_two_modifiers(widget, qtbot):
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClick(widget.button, 'A', modifier = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
    assert widget.button.text() == 'Ctrl+Alt+A ...'

def test_two_letters(widget, qtbot):
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClicks(widget.button, 'AB', modifier = Qt.KeyboardModifier.ControlModifier)
    assert widget.button.text() == 'Ctrl+A, Ctrl+B ...'

    # this is unexpected
    assert widget.button.shortcut().isEmpty()

@pytest.mark.parametrize('ignored_modifier', [
    Qt.KeyboardModifier.KeypadModifier,
    Qt.KeyboardModifier.GroupSwitchModifier,
])
def test_ignored_modifier(ignored_modifier, widget, qtbot):
    """Only a subset of modifiers is supported for keyboard shortcuts"""
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClick(widget.button, 'A', modifier = Qt.KeyboardModifier.ControlModifier | ignored_modifier)
    assert widget.button.text() == 'Ctrl+A ...'

def test_recording_stops(widget, qtbot):
    """How/When recording stops naturally"""
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)
    qtbot.keyClick(widget.button, 'A', modifier = Qt.KeyboardModifier.ControlModifier)

    qtbot.waitSignal(widget.keySequenceChanged)
    pytest.xfail('Find why it doesn\'t stop recording')
    assert not widget.button.isRecording()
    assert widget.button.text() == 'Ctrl+A'

def test_clear_button(widget, qtbot):
    widget.setShortcut(QKeySequence(Qt.Key.Key_Control + Qt.Key.Key_A))

    qtbot.mouseClick(widget.clearButton, Qt.MouseButton.LeftButton)
    assert widget.shortcut().isEmpty()

def test_letter_only(widget, qtbot):
    """Letter key alone doesn't constitute a valid keyboard shortcut"""
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClick(widget.button, 'A')
    assert widget.button.text() == 'Input ...'
    assert widget.shortcut().isEmpty()
    assert widget.button.text() == ''

def test_modifier_only(widget, qtbot):
    """Modifier key alone doesn't constitute a valid keyboard shortcut"""
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClick(widget.button, Qt.Key.Key_Control)

    assert widget.button.text() == 'Ctrl+ ...'
    assert widget.shortcut().isEmpty()
    assert widget.button.text() == ''

def test_max_keystrokes(widget, qtbot):
    """Modifiers are unlimited, other keys limited to 4"""
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClicks(widget.button, 'ABCDE', modifier = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier)
    assert widget.button.text() == 'Ctrl+Alt+Shift+A, Ctrl+Alt+Shift+B, Ctrl+Alt+Shift+C, Ctrl+Alt+Shift+D ...'
    assert not widget.shortcut().isEmpty()

def test_shift_backtab(widget, qtbot):
    """Special handling of a particular combination"""
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClick(widget.button, Qt.Key.Key_Backtab, modifier = Qt.KeyboardModifier.ShiftModifier)
    assert widget.shortcut() == QKeySequence(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Tab))
