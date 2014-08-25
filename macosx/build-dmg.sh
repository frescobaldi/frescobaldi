#!/usr/bin/env bash

if [[ ${MPPREFIX} == '' ]]
then
  MPPREFIX=/opt/local
fi

echo This script will build a standalone Mac application bundle for Frescobaldi
echo and wrap it into a distributable DMG disk image, provided that
echo - you have a working MacPorts installation in ${MPPREFIX},
echo - you installed Frescobaldi\'s dependencies through MacPorts with default
echo ' ' variants \(this also implies that you are using Python 2.7\),
echo - you have working Git, node.js and npm in your \$PATH,
echo - you installed appdmg through npm in global mode \(so it is in your \$PATH\),
echo - you are running this script from the directory macosx of Frescobaldi\'s source.
echo
echo It is strongly recommended that no Python packages are active except for
echo Frescobaldi\'s dependencies.
echo You can achieve this for packages installed through MacPorts with
echo ' ' sudo port deactivate active and not rdepof:frescobaldi and categories:python
echo

VERSION=`${MPPREFIX}/bin/python2.7 -c 'import os
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
echo \(This step will likely give some warnings from /usr/bin/strip about malformed
echo objects and print a long list of missing modules: you can safely ignore them.\)
echo
# The expected warnings are:
# /usr/bin/strip: for architecture x86_64 object: .../dist/Frescobaldi.app/Contents/Frameworks/libgcc_s.1.dylib malformed object (unknown load command 11)
# /usr/bin/strip: object: .../dist/Frescobaldi.app/Contents/MacOS/Frescobaldi malformed object (unknown load command 15)
# /usr/bin/strip: object: .../dist/Frescobaldi.app/Contents/Frameworks/libstdc++.6.dylib malformed object (unknown load command 12)
${MPPREFIX}/bin/python2.7 mac-app.py -v ${VERSION} -a > /dev/null
echo

echo Copying libqsvg.dylib inside the .app bundle.
echo
cp ${MPPREFIX}/share/qt4/plugins/imageformats/libqsvg.dylib dist/Frescobaldi.app/Contents/PlugIns/imageformats/

echo Finalizing the .app bundle with macdeployqt.
echo \(This step will likely give an error about the failed copy of libqsvg.dylib:
echo you can safely ignore it.\)
echo
# The expected error is:
# ERROR: file copy failed from "${MPPREFIX}/share/qt4/plugins/imageformats/libqsvg.dylib" 
# ERROR:  to "dist/Frescobaldi.app/Contents/PlugIns/imageformats/libqsvg.dylib" 
${MPPREFIX}/bin/macdeployqt dist/Frescobaldi.app
echo

if [[ ${NODMG} == 1 ]]
then
  exit
fi

echo Building the DMG disk image with appdmg.
echo
sed -e '/INSTALL/d' ../README > README.txt
cp ../ChangeLog ChangeLog.txt
cp ../COPYING COPYING.txt
APPFILE=`file dist/Frescobaldi.app/Contents/MacOS/Frescobaldi`
APPARCH=''
if [[ ${APPFILE} == *i386* ]]
then
  APPARCH=${APPARCH}-i386
fi
if [[ ${APPFILE} == *x86_64* ]]
then
  APPARCH=${APPARCH}-x86_64
fi
appdmg appdmg/appdmg.json dist/Frescobaldi-${VERSION}${APPARCH}.dmg
rm {README,ChangeLog,COPYING}.txt
