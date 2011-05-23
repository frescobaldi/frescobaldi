# Postinstall script for Windows, run from installer

from __future__ import unicode_literals

import os
import sys

icon = os.path.join(__path__[0], 'frescobaldi.ico')
script = os.path.join(sys.prefix, 'Scripts', 'frescobaldi')
python = os.path.join(sys.exec_prefix, 'pythonw.exe') # because sys.executable points to installer

from frescobaldi_app import info

def welcome():
    """Prints a nice welcome message in the installer."""
    print("\nWelcome to {0} {1}!".format(info.appname, info.version))
    
def shortcut(directory):
    """Makes the Frescobaldi shortcut in the specified directory."""
    lnk = os.path.join(directory, info.appname + ".lnk")
    create_shortcut(
        python,             # path
        info.description,   # description
        lnk,                # link name
        script,             # arguments
        "",                 # workdir
        icon,               # icon
        0,                  # icon index
    )
    file_created(lnk)
    print("Added \"{0}\" to Start Menu".format(info.appname))

def install():
    """Called after installing."""
    # start menu
    for startmenu in (
            get_special_folder_path('CSIDL_COMMON_STARTMENU'),
            get_special_folder_path('CSIDL_STARTMENU'),
            ):
        menudir = os.path.join(startmenu, info.appname)
        if os.path.isdir(menudir):
            shortcut(menudir)
            break
        else:
            try:
                os.mkdir(menudir)
            except OSError:
                continue
            else:
                directory_created(menudir)
                shortcut(menudir)
                break
    welcome()

def remove():
    """Called before uninstalling."""
    pass

