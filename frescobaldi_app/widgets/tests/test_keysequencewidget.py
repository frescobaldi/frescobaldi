# The 'pytest-qt' pytest plugin is required.

import pytest

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

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
    # TODO text

def test_simple_sequence(widget, qtbot):
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)
    assert widget.button.text() == 'Input ...'

    qtbot.keyClick(widget.button, 'A', modifier=Qt.KeyboardModifier.ControlModifier)
    assert not widget.shortcut().isEmpty()
    assert widget.button.text() == 'Ctrl+A'
    assert widget.shortcut() == QKeySequence(Qt.CTRL + Qt.Key_A)

def test_two_modifiers(widget, qtbot):
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClick(widget.button, 'A', modifier=Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.AltModifier)
    assert widget.button.text() == 'Ctrl+Alt+A ...'

def test_two_letters(widget, qtbot):
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClicks(widget.button, 'AB', modifier=Qt.KeyboardModifier.ControlModifier)
    assert widget.button.text() == 'Ctrl+A, Ctrl+B ...'

    pytest.xfail('what does the resulting sequence look like?')
    assert widget.button.shortcut() == QKeySequence(Qt.CTRL + Qt.Key_A + Qt.Key_B)

def test_letter_only(widget, qtbot):
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClick(widget.button, 'A')

    # TODO: this query affects button text!!!
    assert widget.shortcut().isEmpty()

    assert widget.button.text() == ''

def test_modifier_only(widget, qtbot):
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    qtbot.keyClick(widget.button, Qt.Key.Key_Control)

    assert widget.shortcut().isEmpty()
    assert widget.button.text() == ''
