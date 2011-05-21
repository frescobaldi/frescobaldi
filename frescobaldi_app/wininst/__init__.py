# Postinstall script for Windows, run from installer
import os
import sys

icon = os.path.join(__path__[0], 'frescobaldi.ico')
script = os.path.join(sys.prefix, 'Scripts', 'frescobaldi')
python = os.path.join(sys.exec_prefix, 'pythonw.exe') # because sys.executable points to installer




def install():
    """Called after installing."""
    # start menu
    startmenu = get_special_folder_path('CSIDL_STARTMENU')
    dest = os.path.join(startmenu, "Frescobaldi.lnk")
    create_shortcut(
        python,         # path
        "Frescobaldi",  # description
        dest,           # filename
        script,         # arguments
        "",             # workdir
        icon,           # icon
        0,              # icon index
    )
	file_created(dest)
    
def remove():
    """Called before uninstalling."""
    pass

