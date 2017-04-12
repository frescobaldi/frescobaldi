#! python
"""
PostInstall/PostUninstall script for Frescobaldi on Windows

This install script is used by setup.py bdist_wininst

It is called with the '-install' argument after installing, and with the
'-remove' argument _after_ uninstalling.

"""

from __future__ import print_function

import os
import sys


# Windows register:
try:
    import winreg
except ImportError:
    try:
        import _winreg as winreg
    except ImportError:
        winreg = None


# Frescobaldi meta info (Possibly not accessible anymore on uninstall):
try:
    from frescobaldi_app import appinfo
except ImportError:
    appinfo = None


# Icon:
try:
    import frescobaldi_app
    icon = os.path.join(frescobaldi_app.__path__[0], 'icons', 'frescobaldi.ico')
except ImportError:
    icon = None


# Main application script and Python executable:
script = os.path.join(sys.prefix, 'Scripts', 'frescobaldi')
python = os.path.join(sys.exec_prefix, 'pythonw.exe') # because sys.executable points to installer


def install_association():
    """Installs a file association for the LilyPond file type.

    Sets HKEY_CLASSES_ROOT\\LilyPond\\shell\\frescobaldi to 'Open with &Frescobaldi...'
    Sets HKEY_CLASSES_ROOT\\LilyPond\\shell\\frescobaldi\\command
        to '{python} "{script}" "%1"'

    """
    key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "LilyPond\\shell\\frescobaldi")
    with key:
        winreg.SetValue(key, None, winreg.REG_SZ, "Open with &Frescobaldi...")
        winreg.SetValue(key, "command", winreg.REG_SZ, '{0} "{1}" "%1"'.format(python, script))
    print("* Created file association")

def remove_association():
    """Removes the file association.

    Removes HKEY_CLASSES_ROOT\\LilyPond\\shell\\frescobaldi

    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "LilyPond\\shell")
        with key:
            winreg.DeleteKey(key, "frescobaldi\\command")
            winreg.DeleteKey(key, "frescobaldi")
        print("* Removed file association")
    except WindowsError:
        print("*** Could not remove file association ***")

def install_startmenu():
    """Installs a shortcut in the startmenu."""
    for startmenu in (
            get_special_folder_path('CSIDL_COMMON_STARTMENU'),
            get_special_folder_path('CSIDL_STARTMENU'),
            ):
        menudir = os.path.join(startmenu, appinfo.appname)
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

def shortcut(directory):
    """Makes the Frescobaldi shortcut in the specified directory."""
    lnk = os.path.join(directory, appinfo.appname + ".lnk")
    create_shortcut(
        python,              # path
        appinfo.description, # description
        lnk,                 # link name
        script,              # arguments
        "",                  # workdir
        icon,                # icon
        0,                   # icon index
    )
    file_created(lnk)
    print("* Added \"{0}\" to Start Menu".format(appinfo.appname))

def welcome():
    """Prints a nice welcome message in the installer."""
    print("\nWelcome to {0} {1}!".format(appinfo.appname, appinfo.version))


### Main:
if sys.argv[1] == '-install':
    install_startmenu()
    install_association()
    welcome()
elif sys.argv[1] == '-remove':
    remove_association()

