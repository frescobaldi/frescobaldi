# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Export to Music XML
Parsing source to convert to XML
"""

from __future__ import unicode_literals

from PyQt4.QtGui import QTextFormat, QTextCursor

import ly.lex
import highlighter
import textformats
import tokeniter
import info

from . import create_musicxml
from . import ly2xml_mediator
    

class parse_source():
	""" creates the XML-file from the source code according to the Music XML standard """
	
	def __init__(self, doc):
		self.musxml = create_musicxml.create_musicXML()
		self.mediator = ly2xml_mediator.mediator()
		self.prev_command = ''
		self.duration = 4
		self.partname = ''
		self.can_create_part = True
		block = doc.firstBlock()
		while block.isValid():
			for t in tokeniter.tokens(block):
				func_name = t.__class__.__name__ #get instance name
				if func_name != 'Space':
					func_call = getattr(self, func_name)
					func_call(t)
			block = block.next()
		self.iterate_mediator()
		
	def output(self):
		return self.musxml.create_xmldoc()
		
	## 
	# The different source types from ly.lex.lilypond are here sent to translation.
	##				
    	
	def Name(self, token):
		""" name of variable """
		self.partname = token    	
	
	def SequentialStart(self, token):
		""" SequentialStart = { """
		if self.can_create_part:
			self.mediator.new_part(self.partname)
		elif self.prev_command:
			self.mediator.new_from_command(self.prev_command)
		self.can_create_part = False
		
	def SequentialEnd(self, token):
		""" SequentialEnd = } """
		if self.prev_command:
			self.prev_command = ''
		else:
			self.can_create_part = True
			
	def PipeSymbol(self, token):
		""" PipeSymbol = | """
		self.mediator.new_bar()
		
	def Clef(self, token):
		""" Clef \clef"""
		self.prev_command = "clef"
		
	def PitchCommand(self, token):
		if token == '\relative': #the mode must be absolute
			pass #not implemented
		elif token == '\key':
			self.prev_command = "key"
		
	def Note(self, token):
		""" notename, e.g. c, cis, a bes ... """
		if self.prev_command == "key":
			self.key = token
		else:
			self.mediator.new_note(token, self.duration)
		
	def Octave(self, token):
		""" absolute mode required; a number of , or ' or nothing """
		self.mediator.new_octave(token)
		
	def Length(self, token):
		""" note length/duration, e.g. 4, 8, 16 ... """
		self.duration = token
		self.mediator.new_duration(token) 
		
	def EqualSign(self, token):
		pass
		
	def LineComment(self, token):
		pass
		
	def Fraction(self, token):
		print token
		
	def Keyword(self, token):
		self.prev_command = token
		
	def StringQuotedStart(self, token):
		pass
		
	def StringQuotedEnd(self, token):
		pass
		
	def String(self, token):
		pass
		
	def Command(self, token):
		self.prev_command = token
		print "Command:"+token
		
	def UserCommand(self, token):
		if self.prev_command == 'key':
			self.mediator.new_key(self.key, token)
			self.prev_command = ''
		else:
			self.prev_command = token
			print "UserCommand:"+token
		
	def iterate_mediator(self):
		""" the mediator lists are looped through and outputed to the xml-file """
		for part in self.mediator.score:
			self.musxml.create_part('test')
			for bar in part:
				self.musxml.create_measure()
				for obj in bar:
					if isinstance(obj, ly2xml_mediator.bar_attr):
						if obj.has_attr():
							self.musxml.new_bar_attr(obj.clef, obj.time, obj.key, obj.mode, self.mediator.divisions)
					elif isinstance(obj, ly2xml_mediator.bar_note):
						self.musxml.new_note([obj.step, obj.alter, obj.octave], obj.duration, obj.type, self.mediator.divisions)


