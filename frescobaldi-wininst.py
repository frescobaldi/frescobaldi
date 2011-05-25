#! python
"""
PostInstall/PostUninstall script for Frescobaldi on Windows

This install script is used by setup.py bdist_wininst

It is called with the '-install' argument after installing, and with the
'-remove' argument _after_ uninstalling.

"""

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


# Frescobaldi meta info (Not accessible anymore on uninstall):
try:
    from frescobaldi_app import info
except ImportError:
    info = None


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
    
    Sets HKEY_CLASSES_ROOT\\LilyPond\\shell to 'frescobaldi'
    Sets HKEY_CLASSES_ROOT\\LilyPond\\shell\\frescobaldi to 'Open with &Frescobaldi...'
    Sets HKEY_CLASSES_ROOT\\LilyPond\\shell\\frescobaldi\\command
        to '{python} "{script}" "%1"'
    
    """
    key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "LilyPond\\shell")
    with key:
        cmd = winreg.CreateKey(key, "frescobaldi")
        with cmd:
            winreg.SetValue(cmd, None, winreg.REG_SZ, "Open with &Frescobaldi...")
            winreg.SetValue(cmd, "command", winreg.REG_SZ, '{0} "{1}" "%1"'.format(python, script))
        winreg.SetValue(key, None, winreg.REG_SZ, "frescobaldi")
    print("* Created file association")

def remove_association():
    """Removes the file association.
    
    Removes HKEY_CLASSES_ROOT\\LilyPond\\shell\\frescobaldi
    Sets HKEY_CLASSES_ROOT\\LilyPond\\shell to 'generate' (as the LilyPond install does)
    
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "LilyPond")
        with key:
            winreg.DeleteKey(key, "shell\\frescobaldi\\command")
            winreg.DeleteKey(key, "shell\\frescobaldi")
            winreg.SetValue(key, "shell", winreg.REG_SZ, "generate")
    except WindowsError:
        pass

def install_startmenu():
    """Installs a shortcut in the startmenu."""
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
    print("* Added \"{0}\" to Start Menu".format(info.appname))

def welcome():
    """Prints a nice welcome message in the installer."""
    print("\nWelcome to {0} {1}!".format(info.appname, info.version))
    

### Main:
if sys.argv[1] == '-install':
    install_startmenu()
    install_association()
    welcome()
elif sys.argv[1] == '-remove':
    remove_association()

