# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
Resources for styling some widgets.
"""


from PyQt5.QtCore import QDir

QDir.addSearchPath('css', __path__[0])


lcd_screen = """
* {
    border-width: 4 3 2 4;
    border-image: url('css:lcd-borders.png') repeat;
    background-image: url('css:lcd-background.png') repeat;
    color: #151B19;
}
"""

diff_popup = """

/* Question:
 * Is it OK to hard-code the following two generic styles,
 * shouldn't these rather be more specific (cascaded?) classes?
*/

td {
   vertical-align: top;
}

table {
   width: 100%;
}

.border-num-chg {
    color: #3c3b3b;
}

.border-num-ori {
    color: #3c3b3b;
}

/* Question: shouldn't this 'headline' comment be placed earlier? */
/* TODO (not within GSoC): make these styles configurable */

/**
 * DIFF HIGHLIGHTING
 *
 * The following entries apply to the "highlight difference"
 * mode of the popup.
 **/

/* Highlight text, that has been inserted. */
.hi-ins {
    color: #000000;
    background-color: #a9efbc;
}

/* Highlight text, that has been deleted. */
.hi-del {
    color: #000000;
    background-color: #ffdce0;
}

/* Highlight text, that has been inserted and substitutes other text. */
.hi-chg-ins {
    color: #000000;
    background-color: #a9efbc;
}

/* Highlight text, that has been deleted and is substituted by other text. */
.hi-chg-del {
    color: #000000;
    background-color: #ffdce0;
}

"""

