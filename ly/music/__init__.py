# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2014 - 2015 by Wilbert Berendsen
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

r"""
An api to read music from the tokens of a ly.document.Document into a tree
structure.

This is meant to quickly read music from a document, to perform
modifications on the document, and to interpret music and markup and to
convert or export it to other formats.

All nodes are a subclass of items.Item, (which inherits from node.WeakNode).

Tree structures are created from nested LilyPond structures, markup and
scheme code. Some Item types have special methods to query information. The
Music type, for example, has a length() method that returns the duration of
the music fragment.

Using the Music.events() method and the events module, it is possible to
iterate in musical time over the music tree, e.g. to convert music to
another format.

This package is not yet capable to construct documents entirely from scratch.
This needs to be developed. Until that time, the ly.dom module can be used
instead.

Some Item types can have a list of child items, but the tree structure is as
linear as possible.

A convenience function is available to create a ly.music.items.Document
instance for the specified ly.document.Document.

Here is an example::

    >>> import ly.document
    >>> import ly.music
    >>> d=ly.document.Document(r'''
    \version "2.18.0"

    music = \relative {
      \time 4/4
      \key d \minor
      d4 e f g
      a g f e
      d2
    }

    \score {
      \new Staff <<
        \music
      >>
    }
    ''')
    >>> m=ly.music.document(d)
    >>> print(m.dump())
    <Document>
      <Version '\\version'>
        <String '"'>
      <Assignment 'music'>
        <Relative '\\relative'>
          <MusicList '{'>
            <TimeSignature '\\time'>
            <KeySignature '\\key'>
              <Note 'd'>
              <Command '\\minor'>
            <Note 'd'>
            <Note 'e'>
            <Note 'f'>
            <Note 'g'>
            <Note 'a'>
            <Note 'g'>
            <Note 'f'>
            <Note 'e'>
            <Note 'd'>
      <Score '\\score'>
        <Context '\\new'>
          <MusicList '<<'>
            <UserCommand '\\music'>
    >>> m[2][0][0]
    <MusicList '<<'>
    >>> m[2][0][0].length()
    Fraction(5, 2)
    >>>

"""

import ly.document


def document(doc):
    """Return a music.items.Document instance for the ly.document.Document."""
    from . import items
    return items.Document(doc)
