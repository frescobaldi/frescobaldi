% This file is part of the Frescobaldi project, http://www.frescobaldi.org/
%
% Copyright (c) 2011 - 2012 by Wilbert Berendsen
%
% This program is free software; you can redistribute it and/or
% modify it under the terms of the GNU General Public License
% as published by the Free Software Foundation; either version 2
% of the License, or (at your option) any later version.
%
% This program is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
% GNU General Public License for more details.
%
% You should have received a copy of the GNU General Public License
% along with this program; if not, write to the Free Software
% Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
% See http://www.gnu.org/licenses/ for more information.

\version "2.16.2" % absolutely necessary!

\header {
  snippet-title = "Debug Paper Columns"
  snippet-author = "Janek Warchoł"
  snippet-description = \markup {
    Display a lot of information about paper columns
  }
  % add comma-separated tags to make searching more effective:
  tags = "Debugging layout"
  % is this snippet ready?  See meta/status-values.md
  status = "undocumented"
}

% show information about paper-columns:
\layout {
  \override Score.PaperColumn #'stencil = #ly:paper-column::print
  \override Score.NonMusicalPaperColumn #'stencil = #ly:paper-column::print
}
