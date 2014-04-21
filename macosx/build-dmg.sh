#!/usr/bin/env bash

echo This script will build a standalone Mac application bundle for Frescobaldi
echo and wrap it into a distributable DMG disk image, provided that
echo - you have a standard MacPorts installation,
echo - you installed Frescobaldi\'s dependencies, node.js and npm through MacPorts
echo ' ' with default variants \(this also implies that you are using Python 2.7\),
echo - you installed appdmg through npm in global mode,
echo - you have a working Git in your \$PATH,
echo - you are running this script from the directory macosx of Frescobaldi\'s source.
echo
echo It is strongly recommended that no Python packages are active except for
echo Frescobaldi\'s dependencies.
echo You can achieve this for packages installed through MacPorts with
echo ' ' sudo port deactivate active and not rdepof:frescobaldi and categories:python
echo

VERSION=`/opt/local/bin/python2.7 -c 'import os
os.chdir("..")
from frescobaldi_app import info
print info.version'`

if [ v${VERSION} != `git describe` ]
then
  VERSION=${VERSION}-`git log -1 --format=%ci | sed -E 's/^(....)-(..)-(..).*$/\1\2\3/'`
fi

echo The version of the .app bundle will be ${VERSION}.
echo

echo Building the .app bundle with mac-app.py.
echo \(This step will likely give an error from /usr/bin/strip about malformed object
echo .../dist/Frescobaldi.app/Contents/MacOS/Frescobaldi: you can safely ignore it.\)
echo
# The expected error is:
# /usr/bin/strip: object: .../dist/Frescobaldi.app/Contents/MacOS/Frescobaldi malformed object (unknown load command 15)
/opt/local/bin/python2.7 mac-app.py -v ${VERSION} -a > /dev/null
echo

echo Copying libqsvg.dylib inside the .app bundle.
echo
cp /opt/local/share/qt4/plugins/imageformats/libqsvg.dylib dist/Frescobaldi.app/Contents/PlugIns/imageformats/

echo Finalizing the .app bundle with macdeployqt.
echo \(This step will likely give an error about the failed copy of libqsvg.dylib:
echo you can safely ignore it.\)
echo
# The expected error is:
# ERROR: file copy failed from "/opt/local/share/qt4/plugins/imageformats/libqsvg.dylib" 
# ERROR:  to "dist/Frescobaldi.app/Contents/PlugIns/imageformats/libqsvg.dylib" 
/opt/local/bin/macdeployqt dist/Frescobaldi.app
echo

echo Building the DMG disk image with appdmg.
echo
sed -e '/INSTALL/d' ../README > README.txt
cp ../ChangeLog ChangeLog.txt
cp ../COPYING COPYING.txt
/opt/local/bin/appdmg appdmg/appdmg.json dist/Frescobaldi-${VERSION}.dmg
rm {README,ChangeLog,COPYING}.txt
