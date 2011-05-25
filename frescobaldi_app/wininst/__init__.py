# Postinstall script for Windows, run from installer

from __future__ import unicode_literals

import os
import sys

try:
    import winreg
except ImportError:
    try:
        import _winreg as winreg
    except ImportError:
        winreg = None

icon = os.path.join(__path__[0], 'frescobaldi.ico')
script = os.path.join(sys.prefix, 'Scripts', 'frescobaldi')
python = os.path.join(sys.exec_prefix, 'pythonw.exe') # because sys.executable points to installer

from frescobaldi_app import info

def install():
    """Called by the frescobaldi-wininst postinstall script."""
    install_startmenu()
    #install_association()
    welcome()

def remove():
    """Called before uninstalling."""
    #remove_association()

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

def install_association():
    """Installs a file association for the LilyPond file type."""
    key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "LilyPond\\shell")
    with key:
        cmd = winreg.CreateKey(key, "frescobaldi")
        with cmd:
            winreg.SetValue(cmd, None, winreg.REG_SZ, "Open with &Frescobaldi...")
            winreg.SetValue(cmd, "command", winreg.REG_SZ, '{0} "{1}" "%1"'.format(python, script))
        winreg.SetValue(key, None, winreg.REG_SZ, "frescobaldi")
    print("* Created file association")

def remove_association():
    """Removes the file association."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "LilyPond\\shell")
        with key:
            winreg.SetValue(key, None, winreg.REG_SZ, "edit")
            winreg.DeleteKey(key, "frescobaldi\\command")
            winreg.DeleteKey(key, "frescobaldi")
    except WindowsError:
        pass
        
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
    
