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
Frescobaldi main menu.
"""


import builtins

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMenu

import app
import icons
import bookmarkmanager
import documentactions
import documentmenu
import sessions.menu
import pitch
import rest
import rhythm
import lyrics
import panelmanager
import engrave.result_menu
import snippet.menu
import scorewiz
import autocomplete
import sidebar
import matcher
import file_import
import file_export
import browseriface


# postpone translation
_ = lambda *args: lambda: builtins._(*args)


def createMenus(mainwindow):
    """Adds all the menus to the mainwindow's menubar."""
    m = mainwindow.menuBar()

    m.addMenu(menu_file(mainwindow))
    m.addMenu(menu_edit(mainwindow))
    m.addMenu(menu_view(mainwindow))
    m.addMenu(menu_music(mainwindow))
    m.addMenu(menu_snippets(mainwindow))
    m.addMenu(menu_lilypond(mainwindow))
    m.addMenu(menu_tools(mainwindow))
    m.addMenu(menu_document(mainwindow))
    m.addMenu(menu_window(mainwindow))
    m.addMenu(menu_session(mainwindow))
    if app.is_git_controlled():
        from vcs.menu import GitMenu
        m.addMenu(GitMenu(mainwindow))
    m.addMenu(menu_help(mainwindow))


class Menu(QMenu):
    """A QMenu that auto-translates its title by calling a lambda function."""
    def __init__(self, title_func, parent=None):
        """title_func should return the title for the menu when called."""
        super(Menu, self).__init__(parent)
        self.setToolTipsVisible(True)
        self.title_func = title_func
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(self.title_func())


def menu_file(mainwindow):
    m = Menu(_("menu title", "&File"), mainwindow)
    ac = mainwindow.actionCollection

    m.addAction(ac.file_new)
    m.addAction(scorewiz.ScoreWizard.instance(mainwindow).actionCollection.scorewiz)
    m.addMenu(snippet.menu.TemplateMenu(mainwindow))
    m.addSeparator()
    m.addAction(ac.file_open)
    m.addAction(ac.file_open_recent)
    m.addAction(ac.file_insert_file)
    m.addSeparator()
    m.addAction(ac.file_save)
    m.addAction(ac.file_save_as)
    m.addAction(ac.file_save_copy_as)
    m.addAction(panelmanager.manager(mainwindow).snippettool.actionCollection.file_save_as_template)
    m.addAction(ac.file_save_all)
    m.addSeparator()
    m.addAction(ac.file_reload)
    m.addAction(ac.file_reload_all)
    m.addAction(ac.file_external_changes)
    m.addSeparator()
    m.addMenu(menu_file_import(mainwindow))
    m.addMenu(menu_file_export(mainwindow))
    m.addSeparator()
    m.addAction(panelmanager.manager(mainwindow).musicview.actionCollection.music_print)
    m.addAction(ac.file_print_source)
    m.addSeparator()
    m.addAction(ac.file_close)
    m.addAction(ac.file_close_other)
    m.addAction(ac.file_close_all)
    m.addSeparator()
    m.addAction(ac.file_quit)
    if app.is_git_controlled():
        m.addAction(ac.file_restart)
    return m


def menu_file_import(mainwindow):
    m = Menu(_("submenu title", "&Import"), mainwindow)
    ac = file_import.FileImport.instance(mainwindow).actionCollection

    m.addAction(ac.import_all)
    m.addSeparator()
    m.addAction(ac.import_musicxml)
    m.addAction(ac.import_midi)
    m.addAction(ac.import_abc)
    return m


def menu_file_export(mainwindow):
    m = Menu(_("submenu title", "&Export"), mainwindow)
    ac = mainwindow.actionCollection
    acfe = file_export.FileExport.instance(mainwindow).actionCollection

    if app.is_git_controlled() or QSettings().value("experimental-features", False, bool):
        m.addAction(acfe.export_audio)
        m.addAction(acfe.export_musicxml)
    m.addAction(ac.export_colored_html)
    return m


def menu_edit(mainwindow):
    m = Menu(_("menu title", "&Edit"), mainwindow)
    ac = mainwindow.actionCollection

    m.addAction(ac.edit_undo)
    m.addAction(ac.edit_redo)
    m.addSeparator()
    m.addAction(documentactions.get(mainwindow).actionCollection.edit_cut_assign)
    m.addAction(documentactions.get(mainwindow).actionCollection.edit_move_to_include_file)
    m.addAction(ac.edit_cut)
    m.addAction(ac.edit_copy)
    m.addAction(panelmanager.manager(mainwindow).snippettool.actionCollection.copy_to_snippet)
    m.addAction(ac.edit_copy_colored_html)
    m.addAction(ac.edit_paste)
    m.addSeparator()
    m.addAction(ac.edit_select_all)
    m.addAction(ac.edit_select_current_toplevel)
    m.addAction(ac.edit_select_none)
    m.addSeparator()
    m.addAction(ac.edit_find)
    m.addAction(ac.edit_find_next)
    m.addAction(ac.edit_find_previous)
    m.addAction(ac.edit_replace)
    m.addSeparator()
    m.addAction(ac.edit_preferences)
    return m


def menu_view(mainwindow):
    m = Menu(_("menu title", "&View"), mainwindow)
    ac = mainwindow.actionCollection

    m.addAction(ac.view_next_document)
    m.addAction(ac.view_previous_document)
    m.addSeparator()
    m.addAction(ac.view_wrap_lines)
    m.addAction(documentactions.get(mainwindow).actionCollection.view_highlighting)
    m.addAction(sidebar.SideBarManager.instance(mainwindow).actionCollection.view_linenumbers)
    m.addMenu(menu_view_folding(mainwindow))
    m.addSeparator()
    m.addAction(documentactions.get(mainwindow).actionCollection.view_goto_file_or_definition)
    m.addAction(ac.view_goto_line)
    ac = browseriface.get(mainwindow).actionCollection
    m.addAction(ac.go_back)
    m.addAction(ac.go_forward)
    m.addSeparator()
    ac = matcher.Matcher.instance(mainwindow).actionCollection
    m.addAction(ac.view_matching_pair)
    m.addAction(ac.view_matching_pair_select)
    m.addSeparator()
    ac = bookmarkmanager.BookmarkManager.instance(mainwindow).actionCollection
    m.addAction(ac.view_bookmark)
    m.addAction(ac.view_next_mark)
    m.addAction(ac.view_previous_mark)
    m.addAction(ac.view_clear_error_marks)
    m.addAction(ac.view_clear_all_marks)
    m.addSeparator()
    ac = panelmanager.manager(mainwindow).logtool.actionCollection
    m.addAction(ac.log_next_error)
    m.addAction(ac.log_previous_error)
    return m


def menu_view_folding(mainwindow):
    m = Menu(_("submenu title", "&Folding"), mainwindow)
    ac = sidebar.SideBarManager.instance(mainwindow).actionCollection

    m.addAction(ac.folding_enable)
    m.addSeparator()
    m.addAction(ac.folding_fold_current)
    m.addAction(ac.folding_fold_top)
    m.addAction(ac.folding_unfold_current)
    m.addSeparator()
    m.addAction(ac.folding_fold_all)
    m.addAction(ac.folding_unfold_all)
    return m


def menu_music(mainwindow):
    m = Menu(_("menu title", "&Music"), mainwindow)
    ac = panelmanager.manager(mainwindow).musicview.actionCollection

    m.addAction(ac.music_reload)
    m.addSeparator()
    m.addAction(ac.music_zoom_in)
    m.addAction(ac.music_zoom_out)
    m.addAction(ac.music_zoom_original)
    m.addSeparator()
    m.addAction(ac.music_fit_width)
    m.addAction(ac.music_fit_height)
    m.addAction(ac.music_fit_both)
    m.addSeparator()
    m.addAction(ac.music_single_pages)
    m.addAction(ac.music_two_pages_first_right)
    m.addAction(ac.music_two_pages_first_left)
    m.addSeparator()
    m.addAction(ac.music_copy_image)
    m.addAction(ac.music_copy_text)
    m.addSeparator()
    m.addAction(ac.music_jump_to_cursor)
    m.addAction(ac.music_sync_cursor)
    m.addSeparator()
    m.addAction(ac.music_maximize)
    return m


def menu_snippets(mainwindow):
    return snippet.menu.SnippetMenu(mainwindow)


def menu_lilypond(mainwindow):
    m = Menu(_("menu title", "&LilyPond"), mainwindow)
    ac = engrave.engraver(mainwindow).actionCollection

    m.addAction(ac.engrave_sticky)
    m.addAction(ac.engrave_autocompile)
    m.addSeparator()
    m.addAction(ac.engrave_preview)
    m.addAction(ac.engrave_publish)
    m.addAction(ac.engrave_debug)
    m.addAction(ac.engrave_custom)
    m.addAction(ac.engrave_abort)
    m.addSeparator()
    m.addMenu(menu_lilypond_generated_files(mainwindow))
    m.addSeparator()
    m.addAction(ac.engrave_open_lilypond_datadir)
    m.addAction(ac.engrave_show_available_fonts)
    return m


def menu_lilypond_generated_files(mainwindow):
    return engrave.result_menu.Menu(mainwindow)


def menu_tools(mainwindow):
    m = Menu(_('menu title', '&Tools'), mainwindow)

    ac = documentactions.get(mainwindow).actionCollection
    m.addAction(ac.tools_indent_auto)
    m.addAction(ac.tools_indent_indent)
    m.addAction(ac.tools_reformat)
    m.addAction(ac.tools_remove_trailing_whitespace)
    m.addSeparator()
    ac = autocomplete.CompleterManager.instance(mainwindow).actionCollection
    m.addAction(ac.autocomplete)
    m.addAction(ac.popup_completions)
    m.addSeparator()
    m.addMenu(menu_tools_pitch(mainwindow))
    m.addMenu(menu_tools_rest(mainwindow))
    m.addMenu(menu_tools_rhythm(mainwindow))
    m.addMenu(menu_tools_lyrics(mainwindow))
    m.addMenu(menu_tools_quick_remove(mainwindow))
    m.addSeparator()
    ac = documentactions.get(mainwindow).actionCollection
    m.addAction(ac.tools_convert_ly)
    m.addAction(mainwindow.actionCollection.file_open_current_directory)
    m.addAction(mainwindow.actionCollection.file_open_command_prompt)
    m.addSeparator()
    panelmanager.manager(mainwindow).addActionsToMenu(m)
    return m


def menu_tools_lyrics(mainwindow):
    m = Menu(_('submenu title', "&Lyrics"), mainwindow)
    m.setIcon(icons.get('audio-input-microphone'))
    ac = lyrics.lyrics(mainwindow).actionCollection

    m.addAction(ac.lyrics_hyphenate)
    m.addAction(ac.lyrics_dehyphenate)
    m.addSeparator()
    m.addAction(ac.lyrics_copy_dehyphenated)
    return m


def menu_tools_pitch(mainwindow):
    m = Menu(_('submenu title', "&Pitch"), mainwindow)
    m.setIcon(icons.get('tools-pitch'))
    ac = pitch.Pitch.instance(mainwindow).actionCollection

    m.addAction(ac.pitch_language)
    m.addSeparator()
    m.addAction(ac.pitch_relative_assume_first_pitch_absolute)
    m.addAction(ac.pitch_relative_write_startpitch)
    m.addSeparator()
    m.addAction(ac.pitch_rel2abs)
    m.addAction(ac.pitch_abs2rel)
    m.addSeparator()
    m.addAction(ac.pitch_transpose)
    m.addAction(ac.pitch_modal_transpose)
    m.addAction(ac.pitch_mode_shift)
    m.addAction(ac.pitch_simplify)
    return m

def menu_tools_rest(mainwindow):
    m = Menu(_('submenu title', "Rest"), mainwindow)
    m.setIcon(icons.get('tools-rest'))
    ac = rest.Rest.instance(mainwindow).actionCollection

    m.addAction(ac.rest_fmrest2spacer)
    m.addAction(ac.rest_spacer2fmrest)
    m.addSeparator()
    m.addAction(ac.rest_restcomm2rest)
    return m


def menu_tools_rhythm(mainwindow):
    m = Menu(_('submenu title', "&Rhythm"), mainwindow)
    m.setIcon(icons.get('tools-rhythm'))
    ac = rhythm.Rhythm.instance(mainwindow).actionCollection

    m.addAction(ac.rhythm_double)
    m.addAction(ac.rhythm_halve)
    m.addSeparator()
    m.addAction(ac.rhythm_dot)
    m.addAction(ac.rhythm_undot)
    m.addSeparator()
    m.addAction(ac.rhythm_remove_scaling)
    m.addAction(ac.rhythm_remove_fraction_scaling)
    m.addAction(ac.rhythm_remove)
    m.addSeparator()
    m.addAction(ac.rhythm_implicit)
    m.addAction(ac.rhythm_implicit_per_line)
    m.addAction(ac.rhythm_explicit)
    m.addSeparator()
    m.addAction(ac.rhythm_apply)
    m.addAction(ac.rhythm_copy)
    m.addAction(ac.rhythm_paste)
    return m


def menu_tools_quick_remove(mainwindow):
    m = Menu(_('submenu title', "&Quick Remove"), mainwindow)
    m.setIcon(icons.get('edit-clear'))
    ac = documentactions.DocumentActions.instance(mainwindow).actionCollection

    m.addAction(ac.tools_quick_remove_comments)
    m.addAction(ac.tools_quick_remove_articulations)
    m.addAction(ac.tools_quick_remove_ornaments)
    m.addAction(ac.tools_quick_remove_instrument_scripts)
    m.addAction(ac.tools_quick_remove_slurs)
    m.addAction(ac.tools_quick_remove_beams)
    m.addAction(ac.tools_quick_remove_ligatures)
    m.addAction(ac.tools_quick_remove_dynamics)
    m.addAction(ac.tools_quick_remove_fingerings)
    m.addAction(ac.tools_quick_remove_markup)
    return m


def menu_document(mainwindow):
    return documentmenu.DocumentMenu(mainwindow)


def menu_window(mainwindow):
    m = Menu(_('menu title', '&Window'), mainwindow)
    ac = mainwindow.viewManager.actionCollection
    m.addAction(mainwindow.actionCollection.window_new)
    m.addSeparator()
    m.addAction(ac.window_split_horizontal)
    m.addAction(ac.window_split_vertical)
    m.addAction(ac.window_close_view)
    m.addAction(ac.window_close_others)
    m.addAction(ac.window_next_view)
    m.addAction(ac.window_previous_view)
    m.addSeparator()
    m.addAction(mainwindow.actionCollection.window_fullscreen)
    return m


def menu_session(mainwindow):
    return sessions.menu.SessionMenu(mainwindow)


def menu_help(mainwindow):
    m = Menu(_('menu title', '&Help'), mainwindow)
    ac = mainwindow.actionCollection
    m.addAction(ac.help_manual)
    m.addAction(ac.help_whatsthis)
    m.addSeparator()
    m.addAction(panelmanager.manager(mainwindow).docbrowser.actionCollection.help_lilypond_doc)
    m.addAction(panelmanager.manager(mainwindow).docbrowser.actionCollection.help_lilypond_context)
    m.addSeparator()
    m.addAction(ac.help_bugreport)
    m.addSeparator()
    m.addAction(ac.help_about)
    return m


