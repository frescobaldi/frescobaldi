#! python

"""
This script generates HTML pages from the built-in Frescobaldi manual,
for publication on the Frescobaldi web site.

Simply run this from the toplevel frescobaldi directory:

python export-help.py

It creates a help/ directory (by default) and puts the HTML and images there.

"""

from __future__ import unicode_literals

import os
import re
import glob
import time
import shutil

### set output directory here:
output_dir = os.path.abspath('help')

### languages to export help pages for:
export_languages = 'C nl es fr it cs'.split()


### HTML templates for every page to be generated:
templates = {

'C': """\
<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
	<title>{page_title} - Frescobaldi Project</title>
	<link rel="stylesheet" type="text/css" href="/style/1/style.css" />
	<link rel="shortcut icon" type="image/png" href="/favicon.png" />
	<meta http-equiv="Content-Type" content="application/xhtml+xml;charset=utf-8" />
	<meta name="author" content="Wilbert Berendsen" />
	<meta name="description" content="Frescobaldi is a LilyPond sheet music editor" />
	<meta name="keywords" content="lilypond, music notation, ide" />
</head>

<body>

<div id="header">
<h1>{page_title}</h1>
</div>

<div id="sidebar">
	<a accesskey="h" href="/"><u>H</u>ome</a>
	<a accesskey="s" href="screenshots"><u>S</u>creenshots</a>
	<a accesskey="d" href="download"><u>D</u>ownload</a>
	<a accesskey="u" href="uguide" class="selected"><u>U</u>ser Guide</a>
	<a accesskey="v" href="development">De<u>v</u>elopment</a>
	<a accesskey="l" href="links"><u>L</u>inks</a>
</div>

<div id="maincontents">

<p>(<a href="uguide-1">Frescobaldi 1.x User Guide</a>)</p>

{page_contents}

<address>
{page_address}
</address>

</div>

</body>
</html>
""",

"nl": """\
<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="nl" xml:lang="nl">
<head>
	<title>{page_title} - Frescobaldi Project</title>
	<link rel="stylesheet" type="text/css" href="/style/1/style.css" />
	<link rel="shortcut icon" type="image/png" href="/favicon.png" />
	<meta http-equiv="Content-Type" content="application/xhtml+xml;charset=utf-8" />
	<meta name="author" content="Wilbert Berendsen" />
	<meta name="description" content="Frescobaldi is een LilyPond muziek-editor" />
	<meta name="keywords" content="lilypond, music notation, ide" />
</head>

<body>

<div id="header">
<h1>{page_title}</h1>
</div>

<div id="sidebar">
	<a accesskey="h" href="/"><u>H</u>ome</a>
	<a accesskey="s" href="screenshots"><u>S</u>chermafbeeldingen</a>
	<a accesskey="d" href="download"><u>D</u>ownloaden</a>
	<a accesskey="u" href="uguide" class="selected">Gebr<u>u</u>ikershandleiding</a>
	<a accesskey="o" href="development"><u>O</u>ntwikkeling</a>
	<a accesskey="l" href="links"><u>L</u>inks</a>
</div>

<div id="maincontents">

<p>(<a href="uguide-1">Frescobaldi 1.x User Guide</a>)</p>

{page_contents}

<address>
{page_address}
</address>

</div>

</body>
</html>
""",


}



import sip
sip.setapi("QString", 2)
sip.setapi("QVariant", 2)

# make directory
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

# copy images
images = []
images_dir = os.path.join(output_dir, 'images')
images_prefix = 'uguide_'
if not os.path.isdir(images_dir):
    os.makedirs(images_dir)
for img in glob.glob('frescobaldi_app/help/*.png'):
    name = os.path.basename(img)
    images.append(name)
    shutil.copy(img, os.path.join(images_dir, images_prefix + name))

# regexp to adjust links to images in html
images_re = re.compile(
    r'''([Ss][Rr][Cc]\s*=\s*'''
    r'''['"])((?:''' + '|'.join(map(re.escape, images)) + r''')['"])''')

# avoid reading settings
os.environ["XDG_CONFIG_HOME"] = ""

# make frescobaldi_app accessible
import frescobaldi_app.toplevel
import po
import help.helpimpl
import help.contents
import language_names

po.install(None)

# create a MainWindow because of the keyboard shortcuts!
import mainwindow
w = mainwindow.MainWindow()


def set_language(lang):
    """Sets the language. If "C", all text is untranslated."""
    po.install(None if lang == "C" else po.find(lang))


def make_filename(name, lang):
    """Adds the language name to the filename (which must have an extension)."""
    if lang not in ("C", None):
        name = name.replace('.', '.' + lang + '.')
    return name


def make_page(lang):
    """Makes the HTML user guide for the given language."""
    
    html = []
    seen = set()
    
    def add(page, children=None, level=1):
        seen.add(page)
        html.append(
            '<h{1} id="help_{0}"><a name="help_{0}"></a>{2}</h{1}>\n'
            .format(page.name, min(5, level+1), page.title()))
        html.append(help.helpimpl.markexternal(page.body()))
        
        if page.seealso():
            html.append('<p>')
            html.append(_("See also:") + " ")
            html.append(', '.join(p.link() for p in page.seealso()))
            html.append('</p>\n')
        
        for p in children or page.children():
            add(p, None, level+1)

    set_language(lang)
    page = help.contents.contents
    # toc at start
    children = list(page.children())
    children.insert(0, children.pop())
    add(page, children)
    
    left = [page for page in help.helpimpl.all_pages.values()
            if page not in seen and page.name not in ('nohelp', 'page')]
    
    # add pages not in the toc structure
    if left:
        html.append('\n\n<hr />\n\n')
        for page in left:
            add(page, None, 2)
    
    html = ''.join(html)
    
    # make image links work
    html = images_re.sub(
        lambda m: m.group(1) + 'images/' + images_prefix + m.group(2), html)
    
    # make help links work
    html = html.replace('<a href="help:', '<a href="#help_')
    
    others = []
    for l in export_languages:
        if l is not lang:
            others.append('<a href="{0}">{1}</a>'.format(
                make_filename('uguide.html', l),
                "English" if l == "C" else language_names.languageName(l, l),
            ))
    footer = ', '.join(others)
    footer += ' | '
    footer += _("Last Modified: {date}").format(date=time.strftime('%d %b %Y'))
    
    html = templates.get(lang, templates['C']).format(
        page_title = _("Frescobaldi Manual"),
        page_contents = html,
        page_address = footer)
    
    filename = os.path.join(output_dir, make_filename('uguide.html', lang))
    print 'Exporting to:', filename
    with open(filename, 'w') as f:
        f.write(html.encode('utf-8'))


for lang in export_languages:
    make_page(lang)

