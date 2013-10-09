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
Help class between the ly source parser and the XML creator
"""

from __future__ import unicode_literals


class mediator():
	""" Help class between the ly source parser and the XML creator """

	def __init__(self):
		""" create global lists """
		self.score = []
		self.partnames = []
		""" default and initial values """
		self.mustime = [4,4]
		self.clef = ['G',2]
		self.divisions = 1	
		
	def new_part(self, name):
		self.part = []
		self.score.append(self.part)
		self.partnames.append(name)
		self.new_bar()
		self.current_attr.set_time(self.mustime)
		self.current_attr.set_clef(self.clef)	
		
	def new_bar(self):
		self.current_attr = bar_attr()
		self.bar = [self.current_attr]
		self.part.append(self.bar)
		
	def new_key(self, key_name, mode_command):
		mode = mode_command[1:]
		print mode
		self.current_attr.set_key(get_fifths(key_name, mode), mode)		
		
	def new_time(self, fraction):
		self.mustime = fraction.split('/')
		self.current_attr.set_time(self.mustime)
		
	def new_clef(self, clefname):
		self.clef = clefname2clef(clefname)
		self.current_attr.set_clef(self.clef)
		
	def new_note(self, note_name, duration):
		self.current_note = bar_note(note_name, duration)
		self.bar.append(self.current_note)
		self.current_attr = bar_attr()
		
	def new_duration(self, duration):
		self.current_note.set_duration(duration)
		self.check_divs(duration)
		
	def new_octave(self, octave):
		self.current_note.set_octave(octave)
		
	def new_from_command(self, command):
		print command
		
	def check_divs(self, org_len):
		""" The new duration is checked against current divisions """
		divs = self.divisions
		print "Divs:"+str(divs)
		predur, mod = divmod(divs*4,int(org_len))
		if predur == 0:
			self.divisions = int(org_len)/4
			self.check_divs(org_len) #recursive call
		elif mod != 0:
			print "mod:"+str(mod)
			
		
		
class bar_note():
	""" object to keep track of note parameters """
	def __init__(self, note_name, durval):
		plist = notename2step(note_name)
		self.step = plist[0]
		self.alter = plist[1]
		self.octave = 3
		self.duration = durval
		self.type = durval2type(durval)
		
	def set_duration(self, durval):
		self.duration = durval
		self.type = durval2type(durval)
		
	def set_octave(self, octmark):
		self.octave = octmark2oct(octmark)
		
class bar_attr():
	""" object that keep track of bar attributes, e.g. time sign, clef, key etc """
	def __init__(self):
		self.key = -1
		self.time = 0
		self.clef = 0
		
	def set_key(self, muskey, mode):
		self.key = muskey
		self.mode = mode
		
	def set_time(self, mustime):
		self.time = mustime
		
	def set_clef(self, clef):
		self.clef = clef
		
	def has_attr(self):
		check = False	
		if self.key != -1:
			check = True
		elif self.time != 0:
			check = True
		elif self.clef != 0:
			check = True
		return check
		
def get_fifths(key, mode):
	sharpkeys = ['c', 'g', 'd', 'a', 'e', 'b', 'fis', 'cis', 'gis', 'dis', 'ais']
	flatkeys = ['c', 'f', 'bes', 'es', 'as', 'des', 'ges']
	if key in sharpkeys:
		fifths = sharpkeys.index(key)
	elif key in flatkeys:
		fifths = -flatkeys.index(key)
	if mode=='minor':
		return fifths-3
	elif mode=='major':
		return fifths		

def clefname2clef(clefname):
	if clefname == "treble":
		return ['G',2]
	elif clefname == "bass":
		return ['F',4]
	elif clefname == "alt":
		return ['C',3]
		
def notename2step(note_name):
	alter = 0
	if len(note_name)>1:
		is_sharp = note_name.split('i')
		is_flat = note_name.split('e')
		note_name = note_name[0]
		if is_sharp[1]:
			alter = 1
		elif is_flat[1]:
			alter = -1
	return [note_name.upper(), alter]

def durval2type(durval):
	if durval == "1":
		return "whole"
	elif durval == "2":
		return "half"
	elif durval == "4":
		return "quarter"	
	elif durval == "8":
		return "eighth"
	elif durval == "16":
		return "16th"
		
def octmark2oct(octmark):
	if octmark == ",,,":
		return 0
	elif octmark == ",,":
		return 1
	elif octmark == ",":
		return 2
	elif octmark == "'":
		return 4	
	elif octmark == "''":
		return 5
	elif octmark == "'''":
		return 6

	
		
	
