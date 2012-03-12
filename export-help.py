#! python

"""
This script generates HTML pages from the built-in Frescobaldi manual,
for publication on the Frescobaldi web site.

Simply run this from the toplevel frescobaldi directory:

python export-help.py

It creates a help/ directory (by default) and puts the HTML and images there.

"""

import os
import re
import glob
import shutil

### set output directory here:
output_dir = os.path.abspath('help')


import sip
sip.setapi("QString", 2)
sip.setapi("QVariant", 2)




# make directory
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

# copy images
for img in glob.glob('frescobaldi_app/help/*.png'):
    shutil.copy(img, output_dir)

# make frescobaldi_app accessible
import frescobaldi_app.toplevel


# force scheme etc to be default, by avoiding reading settings
import info
info.name = 'dummy'

import po
import help.helpimpl
import help.contents


po.install(None)

# create a MainWindow because of the keyboard shortcuts!
import mainwindow
w = mainwindow.MainWindow()


def set_language(lang):
    """Sets the language. If "C" or None, all text is untranslated."""
    po.install(None if lang in ("C", None) else po.find(lang))


def body(name, lang=None):
    """Returns the HTML body for the given page name and all its children."""
    
    
    html = []
    
    def add(page, level=1):
        html.append(
            '<h{1} id="help_{0}"><a name="help_{0}"></a>{2}</h{1}>\n'
            .format(page.name, min(5, level+1), page.title()))
        html.append(help.helpimpl.markexternal(page.body()))
        
        if page.seealso():
            html.append('<p>')
            html.append(_("See also:") + " ")
            html.append(', '.join(p.link() for p in page.seealso()))
            html.append('</p>\n')
        
        for p in page.children():
            add(p, level+1)




    page = help.helpimpl.all_pages[name]
    set_language(lang)
    add(page)
    
    html = ''.join(html)
    html = html.replace('<a href="help:', '<a href="#help_')
    return html




print body('contents', 'nl').encode('UTF-8')
