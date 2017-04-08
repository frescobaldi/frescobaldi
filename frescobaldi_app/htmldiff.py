# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2012 - 2014 by Wilbert Berendsen
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
Create a HTML diff view from two text strings.
"""


import re
import difflib


def htmldiff(oldtext, newtext, oldtitle="", newtitle="",
             context=True, numlines=3, tabsize=8, wrapcolumn=None):
    """Return a HTML diff from oldtext to newtext.

    See also the Python documentation for difflib.HtmlDiff().make_table().

    """
    table = difflib.HtmlDiff(tabsize=tabsize, wrapcolumn=wrapcolumn).make_table(
        oldtext.splitlines(), newtext.splitlines(),
        oldtitle, newtitle, context, numlines)
    # overcome a QTextBrowser limitation (no text-align css support)
    table = table.replace('<td class="diff_header"', '<td align="right" class="diff_header"')
    # make horizontal lines between sections
    table = re.sub(r'</tbody>\s*<tbody>', '<tr><td colspan="6"><hr/></td></tr>', table)
    legend = _legend.format(
        colors = _("Colors:"),
        added = _("Added"),
        changed = _("Changed"),
        deleted = _("Deleted"),
        links = _("Links:"),
        first_change = _("First Change"),
        next_change = _("Next Change"),
        top = _("Top"))
    return _htmltemplate.format(diff = table, css = _css, legend = legend)


_htmltemplate = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
    <title></title>
    <style type="text/css">{css}</style>
</head>

<body>
    {diff}
    {legend}
</body>
</html>"""

_css = """
    table.diff {
        border:medium;
    }
    .diff_header {
        background-color:#e0e0e0;
    }
    td.diff_header {
        text-align:right;
        padding-right: 10px;
        color: #606060;
    }
    .diff_next {
        background-color:#c0c0c0;
        padding-left: 4px;
        padding-right: 4px;
    }
    .diff_add {
        background-color:#aaffaa;
    }
    .diff_chg {
        background-color:#ffff77;
    }
    .diff_sub {
        background-color:#ffaaaa;
    }
"""

_legend = """<p>
<b>{colors}</b>
<span class="diff_add">&nbsp;{added}&nbsp;</span>,
<span class="diff_chg">&nbsp;{changed}&nbsp;</span>,
<span class="diff_sub">&nbsp;{deleted}&nbsp;</span>
<br />
<b>{links}</b>
f: {first_change},
n: {next_change},
t: {top}
</p>
"""

