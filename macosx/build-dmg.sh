#!/usr/bin/env bash

read -d '' INTRO <<- EOF
Build a standalone Mac application bundle for Frescobaldi
and wrap it into a distributable DMG disk image.

Prerequisites:
- Frescobaldi's dependencies installed through MacPorts with default variants,
  for the requested architecture set,
- \$PATH contains Git, appdmg (a node.js/npm package) and OpenSSL with
  SHA256 support.

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
from frescobaldi_app import appinfo
print appinfo.version'`

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

APPBUNDLE=dist/Frescobaldi.app

echo Copying libqsvg.dylib inside the .app bundle.
echo
cp ${MPPREFIX}/libexec/qt4/share/plugins/imageformats/libqsvg.dylib ${APPBUNDLE}/Contents/PlugIns/imageformats/

echo Finalizing the .app bundle with macdeployqt.
echo \(This step will likely give an error about the failed copy of libqsvg.dylib:
echo you can safely ignore it.\)
echo
# The expected error is:
# ERROR: file copy failed from "${MPPREFIX}/share/qt4/plugins/imageformats/libqsvg.dylib" 
# ERROR:  to "dist/Frescobaldi.app/Contents/PlugIns/imageformats/libqsvg.dylib" 
${MPPREFIX}/libexec/qt4/bin/macdeployqt ${APPBUNDLE}
echo

MACHO=`find ${APPBUNDLE} -type f -exec file {} + | grep Mach-O`
NON32=`echo "${MACHO}" | grep -v i386`
NON64=`echo "${MACHO}" | grep -v x86_64`
if [[ ${NON32} == '' ]]
then
  if [[ ${NON64} == '' ]]
  then
    APPARCH=intel
  else
    APPARCH=i386
    if [[ ${NON64} != ${MACHO} ]]
    then
      MIXEDINTEL=1
    fi
  fi
else
  if [[ ${NON64} == '' ]]
  then
    APPARCH=x86_64
    if [[ ${NON32} != ${MACHO} ]]
    then
      MIXEDINTEL=1
    fi
  else
    APPARCH=unknown
  fi
fi
if [[ ${APPARCH} == unknown ]]
then
  echo "Error: unknown binary architecture set." 1>&2
  echo "The .app bundle might be broken." 1>&2
  exit 1
else
  if [[ ${ARCH} != '' && ${ARCH} != ${APPARCH} ]]
  then
    if [[ ${APPARCH} == intel && ( ${ARCH} == i386 || ${ARCH} == x86_64 ) ]]
    then
      echo "Warning: binary architecture set mismatch." 1>&2
      echo "The requested architecture ${ARCH} is included in the application bundle," 1>&2
      echo "but you are probably including a lot more than it is necessary." 1>&2
      echo "The apparent architecture set of the .app bundle is ${APPARCH}." 1>&2
    else
      echo "Error: binary architecture set mismatch." 1>&2
      echo "You requested ${ARCH}, but the apparent architecture set is ${APPARCH}." 1>&2
      exit 1
    fi
  else
    if [[ ${ARCH} != '' ]]
    then
      ASREQUESTED=", as requested"
    fi
    if [[ ${MIXEDINTEL} == 1 ]]
    then
      echo "Warning: mixed binary architecture." 1>&2
      echo "The apparent architecture set of the .app bundle is ${APPARCH}${ASREQUESTED}," 1>&2
      echo "but some Mach-O files contain both i386 and x86_64 code." 1>&2
    else
      echo "The apparent architecture set of the .app bundle is ${APPARCH}${ASREQUESTED}."
    fi
  fi
fi
echo "The .app bundle is ready: ${APPBUNDLE}"

if [[ ${NODMG} == 1 ]]
then
  exit
fi
echo

echo Building the DMG disk image with appdmg.
echo
DMGNAME=Frescobaldi-${VERSION}-${APPARCH}.dmg
sed -e '/INSTALL/d' ../README.md > README.txt
cp ../ChangeLog ChangeLog.txt
cp ../COPYING COPYING.txt
appdmg --quiet appdmg/appdmg.json dist/${DMGNAME}
cd dist
openssl sha256 ${DMGNAME} > ${DMGNAME}.sha256
cd ..
rm {README,ChangeLog,COPYING}.txt

if [[ $? == 0 ]]
then
  echo "The disk image is ready: dist/${DMGNAME}"
fi
