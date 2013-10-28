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

\version "2.16.2"

\header {
  snippet-title = "Voice colors"
  snippet-author = "Janek Warchoł, Urs Liska"
  snippet-description = \markup {
    This snippet redefines the commands
    "\voiceOne" to "\voiceFour" so that voices explicitly set
    with them are colored.
    NOTE:
    - When used in conjunction with 'color-directions'
      there may be side-effects.
      In particular the "\oneVoice" and the "\xxxNeutral"
      commands revert the other functions' colors too.
  }
  % add comma-separated tags to make searching more effective:
  tags = "color, preview, frescobaldi"
  % is this snippet ready?  See meta/status-values.md
  status = "ready" % aiming to be 'official'
}

% Define appearance
#(cond ((not (defined? 'debug-voice-one-color))
        (define debug-voice-one-color darkred)))
#(cond ((not (defined? 'debug-voice-two-color))
        (define debug-voice-two-color darkblue)))
#(cond ((not (defined? 'debug-voice-three-color))
        (define debug-voice-three-color darkgreen)))
#(cond ((not (defined? 'debug-voice-four-color))
        (define debug-voice-four-color darkmagenta)))


%%%%%%%%%%%%%%%%%%%%%%%%%%
% here goes the snippet: %
%%%%%%%%%%%%%%%%%%%%%%%%%%

\include "color-voice.ily"

voiceOne = {
  \voiceOne
  \colorVoice #debug-voice-one-color
}

voiceTwo = {
  \voiceTwo
  \colorVoice #debug-voice-two-color
}

voiceThree = {
  \voiceThree
  \colorVoice #debug-voice-three-color
}

voiceFour = {
  \voiceFour
  \colorVoice #debug-voice-four-color
}

oneVoice = {
  \oneVoice
  \unColorVoice
}
