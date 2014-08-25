#!/usr/bin/env bash

read -d '' INTRO <<- EOF
Build a standalone Mac application bundle for Frescobaldi
and wrap it into a distributable DMG disk image.

Prerequisites:
- Frescobaldi's dependencies installed through MacPorts with default variants,
  for the requested architecture set,
- \$PATH contains Git and appdmg (a node.js/npm package).

It is strongly recommended that no Python packages are active except for
Frescobaldi's dependencies.
You can achieve this for packages installed through MacPorts with
  sudo port deactivate active and not rdepof:frescobaldi and categories:python
EOF

if [[ ./`basename $0` != $0 ]]
then
  echo "Error: wrong working directory." 1>&2
  echo "You must run "`basename $0`" from the macosx directory of Frescobaldi's source." 1>&2
  exit 1
fi

if [[ ${MPPREFIX} == '' ]]
then
  MPPREFIX=/opt/local
fi

echo "${INTRO}"
echo

VERSION=`${MPPREFIX}/bin/python2.7 -c 'import os
os.chdir("..")
from frescobaldi_app import info
print info.version'`

if git rev-parse --git-dir > /dev/null 2>&1
then
  if [[ v${VERSION} != `git describe` ]]
  then
    VERSION=${VERSION}-`git log -1 --format=%ci | sed -E 's/^(....)-(..)-(..).*$/\1\2\3/'`
  fi
else
  echo "Warning: you are not running "`basename $0`" from the Git repository."
  echo "The version of the .app bundle could be wrong or incomplete if you are"
  echo "not building from the source of a tagged release."
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
