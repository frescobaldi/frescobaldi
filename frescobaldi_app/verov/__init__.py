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
A proof-of-concept module for testing the use of Verovio in Frescobaldi.
In order to work the Verovio Python module has to be compiled and installed
on the system.
Download the source from https://github.com/rism-ch/verovio/releases
(or clone the repository) and install the module (system-wide) with
   $ cd python
   $ python3 setup.py build_ext
   $ sudo python3 setup.py install
(as described at
https://github.com/rism-ch/verovio/wiki/Building-instructions#building-the-python-toolkit)
"""

import os
import verovio

# We have added a sample MEI file in the module directory
verovio_dir = os.path.dirname(__file__)
sample_file = os.path.join(verovio_dir, 'Bach_Ein_festeBurg.mei')

# Load Verovio
ver_tk = verovio.toolkit( False )

### TODO ###
# uncomment the following line and set the path appropriately!
#ver_tk.setResourcePath('/path/to/verovio/data')

# Let Verovio parse the file
ver_tk.loadFile(sample_file)
from pathlib import Path
home = str(Path.home())

# Create the score and save it in the user's home directory
ver_tk.renderToSvgFile(os.path.join(home, "Verovio-export-sample.svg"), 1)



