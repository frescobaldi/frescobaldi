# Postinstall script for Windows, run from installer
import os
import sys

icon = os.path.join(__path__[0], 'frescobaldi.ico')
script = os.path.join(sys.prefix, 'scripts', 'frescobaldi')
python = os.path.join(sys.prefix, 'pythonw.exe') # because sys.executable points to installer




def install():
    """Called after installing."""
    # start menu
    startmenu = get_special_folder_path('CSIDL_STARTMENU')
    dest = os.path.join(startmenu, "frescobaldi.lnk")
    create_shortcut(
        python,         # path
        "Frescobaldi",  # description
        dest,           # filename
        "",             # arguments
        "",             # workdir
        icon,           # icon
        0,              # icon index
    )
    
def remove():
    """Called before uninstalling."""
    pass

