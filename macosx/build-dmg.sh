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

read -d '' USAGE <<- EOF
Usage: $0 [-p <MacPorts prefix>] [-a <architecture set>] [-d] [-h]
  -p defaults to /opt/local
  -a defaults to the architecture of the current Python binary
  -d = do not build the DMG disk image
  -h = show this help
  <architecture set> must be either i386, x86_64 or intel (= i386 + x86_64)
EOF

MPPREFIX=/opt/local

while getopts ":p:a:dh" opt; do
  case ${opt} in
    p)
      MPPREFIX=${OPTARG}
      ;;
    a)
      ARCH=${OPTARG}
      ARCHOPT='-r '${ARCH}
      ;;
    d)
      NODMG=1
      ;;
    h)
      echo "${INTRO}"
      echo
      echo "${USAGE}"
      exit
      ;;
    *)
      echo "${INTRO}" 1>&2
      echo 1>&2
      echo "${USAGE}" 1>&2
      exit 1
      ;;
  esac
done

if [[ ./`basename $0` != $0 ]]
then
  echo "Error: wrong working directory." 1>&2
  echo "You must run "`basename $0`" from the macosx directory of Frescobaldi's source." 1>&2
  exit 1
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
${MPPREFIX}/bin/python2.7 mac-app.py -v ${VERSION} -a ${ARCHOPT} > /dev/null
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

APPFILE=`file dist/Frescobaldi.app/Contents/MacOS/Frescobaldi`
if [[ ${APPFILE} == *i386* ]]
then
  if [[ ${APPFILE} == *x86_64* ]]
  then
    APPARCH=intel
  else
    APPARCH=i386
  fi
else
  if [[ ${APPFILE} == *x86_64* ]]
  then
    APPARCH=x86_64
  else
    APPARCH=unknown
  fi
fi
if [[ ${ARCH} != '' ]]
then
  if [[ ${ARCH} != ${APPARCH} ]]
  then
    echo "Error: binary architecture set mismatch." 1>&2
    echo "You requested ${ARCH}, but the apparent architecture set is ${APPARCH}." 1>&2
    exit 1
  fi
else
  if [[ ${APPARCH} == unknown ]]
  then
    echo "Error: binary architecture set unknown." 1>&2
    echo "The .app bundle might be broken." 1>&2
    exit 1
  fi
  echo "The apparent architecture set of the .app bundle is ${APPARCH}."
  echo
fi

if [[ ${NODMG} == 1 ]]
then
  exit
fi

echo Building the DMG disk image with appdmg.
echo
sed -e '/INSTALL/d' ../README > README.txt
cp ../ChangeLog ChangeLog.txt
cp ../COPYING COPYING.txt
appdmg appdmg/appdmg.json dist/Frescobaldi-${VERSION}-${APPARCH}.dmg
rm {README,ChangeLog,COPYING}.txt
