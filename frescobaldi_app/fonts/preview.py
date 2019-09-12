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
Show a music sample preview.
"""


import os
import re
import tempfile

from PyQt5.QtCore import (
    QSettings,
    Qt
)
from PyQt5.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

import app
import appinfo
import musicpreview
import util
import widgets.urlrequester


def get_persistent_cache_dir():
    """
    Determine location for "persistent" caching of music fonts,
    either from the Preference (persistent) or the default temporary
    directory, which will be purged upon computer shutdown.
    """
    pref = QSettings().value('music-fonts/font-cache', '', str)
    return pref or os.path.join(
        tempfile.gettempdir(),
        appinfo.name + '-music-font-samples'
    )


class FontsPreviewWidget(QWidget):
    """Show a preview score using the font selection."""

    # Permanently cache compilations of the provided samples
    persistent_cache_dir = get_persistent_cache_dir()
    # Cache compilations of custom samples for Frescobaldi's lifetime only
    temp_dir = util.tempdir()

    def __init__(self, parent):
        super(FontsPreviewWidget, self).__init__(parent)

        # Create the cache directory for default samples
        os.makedirs(self.persistent_cache_dir, 0o700, exist_ok=True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Overall sample target button group
        self.sample_button_group = sbg = QButtonGroup()
        self.rb_default = QRadioButton()
        self.rb_custom = QRadioButton()
        self.rb_current = QRadioButton()
        sbg.addButton(self.rb_default, 0)
        sbg.addButton(self.rb_custom, 1)
        sbg.addButton(self.rb_current, 2)

        # ComboBox for provided default samples
        self.cb_default_sample = QComboBox()
        self.populate_default_samples()

        # Select custom file
        self.custom_sample_url = widgets.urlrequester.UrlRequester(
            fileMode=QFileDialog.ExistingFile,
            mustExist=True
        )


        # Add sample source widgets to layout
        bl = QHBoxLayout()
        bl.addWidget(self.rb_default)
        bl.addWidget(self.cb_default_sample)
        bl.addWidget(self.rb_custom)
        bl.addWidget(self.custom_sample_url)
        bl.addWidget(self.rb_current)
        layout.addLayout(bl)

        # The score preview widget
        self.musicFontPreview = mfp = musicpreview.MusicPreviewWidget(
            parent,
            showProgress=False,
            showWaiting=True,
            showLog=False
        )
        layout.addWidget(mfp)

        app.translateUI(self)
        self.loadSettings()

        # Trigger showing of new samples
        sbg.buttonToggled.connect(self.set_music_sample_source)
        self.cb_default_sample.currentIndexChanged.connect(
            self.select_default_sample
        )
        self.custom_sample_url.editingFinished.connect(self.show_sample)

        parent.finished.connect(self.saveSettings)

    def translateUI(self):
        self.rb_default.setText(_("&Default"))
        self.rb_default.setToolTip(_("Choose default music font sample"))
        self.rb_custom.setText(_("&Custom"))
        self.rb_custom.setToolTip(_(
            "Use custom sample for music font.\n"
            + "NOTE: This should not include a version statement "
            + "or a paper block."
        ))
        self.rb_current.setText(_("C&urrent"))
        self.rb_current.setToolTip(
            _(
                "Use current document as music font sample.\n"
                + "NOTE: This is not robust if the document contains "
                + "a \\paper { } block."
                ))
        csu = self.custom_sample_url
        csu.setDialogTitle(_("Select sample score"))
        csu.fileDialog(True).setNameFilters(['LilyPond files (*.ly)'])

    def loadSettings(self):
        s = QSettings()
        s.beginGroup('document-fonts-dialog')
        id = s.value('sample-source-button', 0, int)
        self.sample_button_group.button(id).setChecked(True)
        default_sample = s.value('default-music-sample', '', str)
        index = max(0, self.cb_default_sample.findText(default_sample))
        self.cb_default_sample.setCurrentIndex(index)
        custom_sample = s.value('custom-music-sample-url', '')
        self.custom_sample_url.setPath(custom_sample)
        sample_dir = (
            os.path.dirname(custom_sample) if custom_sample
            else os.path.dirname(
                self.window().parent().currentDocument().url().toLocalFile())
        )
        self.custom_sample_url.fileDialog().setDirectory(sample_dir)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup('document-fonts-dialog')
        s.setValue(
            'sample-source-button', self.sample_button_group.checkedId()
        )
        s.setValue(
            'default-music-sample', self.cb_default_sample.currentText()
        )
        s.setValue('custom-music-sample-url', self.custom_sample_url.path())

    def populate_default_samples(self):
        """Populate hte default samples ComboBox.
        This is just factored out to unclutter __init__.
        """
        cb = self.cb_default_sample

        def add_entry(entry):
            cb.addItem(entry['label'], entry['file'])
            cb.setItemData(cb.count() - 1, entry['tooltip'], Qt.ToolTipRole)

        add_entry({
            'label': _('Bach (Piano)'),
            'file': 'bach.ly',
            'tooltip': _(
                "Baroque music lends itself to traditional fonts"
            )
        })
        add_entry({
            'label': _('Scriabine (Piano)'),
            'file': 'scriabine.ly',
            'tooltip': _(
                "Late romantic, complex piano music"
            )
        })
        add_entry({
            'label': _('Berg (String Quartet)'),
            'file': 'berg-string-quartet.ly',
            'tooltip': _(
                "Complex score, requires a 'clean' font"
            )
        })
        add_entry({
            'label': _('Real Book (Lead Sheet)'),
            'file': 'realbook.ly',
            'tooltip': _(
                "Jazz-like lead sheet.\n"
                + "NOTE: beautiful results rely on appropriate text fonts.\n"
                + "Good choices are “lilyjazz-text” for roman and\n"
                + "“lilyjazz-chords” for sans text fonts."
            )
        })
        add_entry({
            'label': _('Glyphs'),
            'file': 'glyphs.ly',
            'tooltip': _(
                "Non-comprehensive specimen sheet"
            )
        })

    def select_default_sample(self):
        """Called when a new default sample has been selected."""
        if self.sample_button_group.checkedId() > 0:
            self.rb_default.setChecked(True)
            self.set_music_sample_source()
        else:
            self.show_sample()

    def set_music_sample_source(self):
        """
        Update interface to access default samples or custom file chooser.
        """
        button_id = self.sample_button_group.checkedId()
        self.custom_sample_url.setEnabled(button_id == 1)
        self.show_sample()

    def show_sample(self):
        """Display a sample document for the selected notation font."""
        print("Enter show_sample")
        global_size = ''
        base_dir = None
        sample_content = ''
        cache_persistently = False

        def handle_staff_size():
            """
            If the sample file *starts with* a staff-size definition
            it will be injected *after* our paper block.
            """
            nonlocal sample_content, global_size
            match = re.match('#\(set-global-staff-size \d+\)', sample_content)
            if match:
                global_size = match.group(0)
                sample_content = sample_content[len(global_size):]

        def load_content():
            """
            Load the content to be engraved as sample,
            either from the active editor or from a file.
            """
            nonlocal sample_content, base_dir
            nonlocal cache_persistently
            custom_file = self.custom_sample_url.path()

            # target will be one out of
            # 0: provided sample file
            # 1: custom file
            # 2: active document (unsaved state)
            target = self.sample_button_group.checkedId()
            if target == 1 and not custom_file:
                # Custom file selected but no file provided
                target = 0

            # Provided sample files will be cached persistently
            cache_persistently = target == 0

            if target == 2:
                # Engrave active document
                import engrave
                current_doc = engrave.engraver(app.activeWindow()).document()
                sample_content = current_doc.toPlainText()
                if not current_doc.url().isEmpty():
                    base_dir = os.path.dirname(current_doc.url().toLocalFile())
            else:
                if target == 1:
                    print("Custom file:", custom_file)
                    sample_file = custom_file
                else:
                    # Engrave from a file
                    import fonts
                    template_dir = os.path.join(fonts.__path__[0], 'templates')
                    sample_file = os.path.join(
                        template_dir,
                        'musicfont-' + self.cb_default_sample.currentData()
                    )
                    print("Default:", sample_file)
                base_dir = os.path.dirname(sample_file)
                with open(sample_file, 'r') as f:
                    sample_content = f.read()

        def sample_document():
            """
            Steps of composing the used sample document.
            """
            load_content()
            handle_staff_size()
            result = [
                '\\version "{}"\n'.format(
                    self.window().available_fonts.music_fonts(
                    ).lilypond_info.versionString()
                ),
                '{}\n'.format(global_size) if global_size else '',
                # TODO: "Protect" this regarding openLilyLib.
                # It would be easy to simply pass 'lily' as an argument
                # to always use the generic approach. However, that would
                # prevent the use of font extensions and stylesheets.
                self.window().font_full_cmd(),
                sample_content
            ]
            return '\n'.join(result)

        sample = sample_document()
        cache_dir = (
            self.persistent_cache_dir
            if cache_persistently
            else self.temp_dir
        )
        self.musicFontPreview.preview(
            sample,
            title='Music font preview',
            base_dir=base_dir,
            temp_dir=cache_dir,
            cached=True)
