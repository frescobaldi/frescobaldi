#!/usr/bin/env bash

PYTHON_VERSION=3.10
PYTHON="/opt/local/bin/python${PYTHON_VERSION}"
QTROOT='/opt/local/libexec/qt5'

PYTHON_PREFIX=$(${PYTHON} -c 'import sys; print(sys.prefix)')
PYTHON_DIR_TO_PATCH="lib/python${PYTHON_VERSION}/site-packages/PyQt5/uic"
PYTHON_PATCH_FILE='patch-PyQt5-uic.diff'

read -d '' INTRO <<- EOF
Build a standalone Mac application bundle for Frescobaldi
and wrap it into a distributable DMG disk image.

Prerequisites:
- Frescobaldi's dependencies installed through MacPorts with default variants,
  for the requested architecture set,
- \$PATH contains Git, appdmg (a node.js/npm package) and OpenSSL with
  SHA256 support,
- due to a bug in py2app, PyQt5 needs to be patched by applying the patch file
  ${PYTHON_PATCH_FILE} in the directory ${PYTHON_DIR_TO_PATCH}
  of the Python.framework corresponding to the used Python, e.g., with
    sudo patch -d${PYTHON_PREFIX}/${PYTHON_DIR_TO_PATCH} -p0 < ${PYTHON_PATCH_FILE}

It is strongly recommended that no Python packages are active except for
Frescobaldi's dependencies.
You can achieve this for packages installed through MacPorts with
  sudo port deactivate active and not rdepof:frescobaldi and categories:python
It is also recommended to deactivate Frescobaldi itself:
  sudo port deactivate frescobaldi
Moreover, due to a problem with packaging PyQtWebEngine (see #1244), as a
temporary workaround it is recommended to deactivate it:
  sudo port deactivate py${PYTHON_VERSION//.}-pyqt5-webengine qt5-qtwebengine
EOF

read -d '' USAGE <<- EOF
Usage: $0 [-P <Python executable>] [-Q <root of Qt installation>]
          [-a <architecture set>] [-v] [-d] [-h]
  -P defaults to ${PYTHON}
  -Q defaults to ${QTROOT}
  -a defaults to the architecture of the current Python binary
  -v = show output of mac-app.py
  -d = do not build the DMG disk image
  -h = show this help
  <architecture set> must be one of the following:
    x86_64, arm64, universal2
EOF

while getopts ":P:Q:a:vdh" opt; do
  case ${opt} in
    P)
      PYTHON=${OPTARG}
      ;;
    Q)
      QTROOT=${OPTARG}
      ;;
    a)
      ARCH=${OPTARG}
      ARCHOPT='-r '${ARCH}
      ;;
    v)
      VERBOSE=1
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

if [[ ./$(basename $0) != $0 ]]
then
  echo "Error: wrong working directory." 1>&2
  echo "You must run "$(basename $0)" from the macosx directory of Frescobaldi's source." 1>&2
  exit 1
fi

echo "${INTRO}"
echo

VERSION=$(${PYTHON} -c 'import os
os.chdir("..")
from frescobaldi_app import appinfo
print(appinfo.version)')

if git rev-parse --git-dir > /dev/null 2>&1
then
  if [[ v${VERSION} != $(git describe --tags) ]]
  then
    VERSION=${VERSION}-$(git log -1 --format=%ci | sed -E 's/^(....)-(..)-(..).*$/\1\2\3/')
  fi
else
  echo "Warning: you are not running "$(basename $0)" from the Git repository." 1>&2
  echo "The version of the .app bundle could be wrong or incomplete if you are" 1>&2
  echo "not building from the source of a tagged release." 1>&2
fi

echo The version of the .app bundle will be ${VERSION}.
echo

echo "Do you want to continue?"
CONTINUE=''
echo -n "Type y or Y for yes, anything else for no: "
read CONTINUE
echo
if [[ "$CONTINUE" != 'y' && "$CONTINUE" != 'Y' ]]
then
  exit
fi

echo Building the .app bundle with mac-app.py.
echo \(This step will likely give some warnings from /usr/bin/strip about malformed
echo objects and print a long list of missing modules: you can safely ignore them.\)
echo
# The expected warnings are:
# /usr/bin/strip: for architecture x86_64 object: .../dist/Frescobaldi.app/Contents/Frameworks/libgcc_s.1.dylib malformed object (unknown load command 11)
# /usr/bin/strip: object: .../dist/Frescobaldi.app/Contents/MacOS/Frescobaldi malformed object (unknown load command 15)
# /usr/bin/strip: object: .../dist/Frescobaldi.app/Contents/Frameworks/libstdc++.6.dylib malformed object (unknown load command 12)
if [[ "${VERBOSE}" == 1 ]]
then
  ${PYTHON} mac-app.py -v ${VERSION} -a ${ARCHOPT}
else
  ${PYTHON} mac-app.py -v ${VERSION} -a ${ARCHOPT} > /dev/null
fi
echo

APPBUNDLE=dist/Frescobaldi.app

check_fix_appbundle () {
  # $1 string: path to .app bundle
  # $2 string: requested architecture, if any, or empty string
  # $3 boolean: propose to fix mixed?
  local MACHO=$(find $1 -type f -exec file {} + | grep Mach-O)
  local NOT_x86_64=$(echo "${MACHO}" | grep -v x86_64)
  local NOT_arm64=$(echo "${MACHO}" | grep -v arm64)
  local MIXED=''
  if [[ "${NOT_arm64}" == '' ]]
  then
    if [[ "${NOT_x86_64}" == '' ]]
    then
      APPARCH=universal2
    else
      APPARCH=arm64
      if [[ "${NOT_x86_64}" != "${MACHO}" ]]
      then
        MIXED=1
      fi
    fi
  else
    if [[ "${NOT_x86_64}" == '' ]]
    then
      APPARCH=x86_64
      if [[ "${NOT_arm64}" != "${MACHO}" ]]
      then
        MIXED=1
      fi
    else
      APPARCH=unknown
    fi
  fi
  if [[ "${APPARCH}" == unknown ]]
  then
    echo "Error: unknown binary architecture set." 1>&2
    echo "The .app bundle might be broken." 1>&2
    return 1
  else
    if [[ "$2" != '' && "$2" != "${APPARCH}" ]]
    then
      if [[ "${APPARCH}" == universal2 && ( "$2" == x86_64 || "$2" == arm64 ) ]]
      then
        echo "Warning: binary architecture set mismatch." 1>&2
        echo "The requested architecture $2 is included in the application bundle," 1>&2
        echo "but you are probably including a lot more than it is necessary." 1>&2
        echo "The apparent architecture set of the .app bundle is ${APPARCH}." 1>&2
      else
        echo "Error: binary architecture set mismatch." 1>&2
        echo "You requested $2, but the apparent architecture set is ${APPARCH}." 1>&2
        return 1
      fi
    else
      if [[ "$2" != '' ]]
      then
        ASREQUESTED=", as requested"
      fi
      if [[ "${MIXED}" == 1 ]]
      then
        echo "Warning: mixed binary architecture." 1>&2
        echo "The apparent architecture set of the .app bundle is ${APPARCH}${ASREQUESTED}," 1>&2
        echo "but some Mach-O files contain both x86_64 and arm64 code." 1>&2
        if [[ "$3" ]]
        then
          echo
          echo "Do you want to fix the .app bundle by keeping only the ${APPARCH} code?"
          local FIX_APPBUNDLE=''
          echo -n "Type y or Y for yes, anything else for no: "
          read FIX_APPBUNDLE
          echo
          if [[ "$FIX_APPBUNDLE" == 'y' || "$FIX_APPBUNDLE" == 'Y' ]]
          then
            mv $1 $1.mixed
            ditto --arch ${APPARCH} $1.mixed $1
            rm -r $1.mixed
            check_fix_appbundle "$1" "$2" ''
          fi
        fi
      else
        echo "The apparent architecture set of the .app bundle is ${APPARCH}${ASREQUESTED}."
      fi
    fi
  fi
}

check_fix_appbundle "${APPBUNDLE}" "${ARCH}" 1

if [[ $? != 0 ]]
then
  exit 1
fi

echo "The .app bundle is ready: ${APPBUNDLE}"

if [[ "${NODMG}" == 1 ]]
then
  exit 0
fi
echo

echo Building the DMG disk image with appdmg.
echo
DMGNAME=Frescobaldi-${VERSION}-${APPARCH}.dmg
sed -e '/INSTALL/d' ../README.md > README.txt
cp ../CHANGELOG.md CHANGELOG.txt
cp ../COPYING COPYING.txt
appdmg --quiet appdmg/appdmg.json dist/${DMGNAME}
APPDMG_EXITSTATUS=$?
if [[ "${APPDMG_EXITSTATUS}" != 0 ]]
then
  exit 1
fi
cd dist
openssl sha256 ${DMGNAME} > ${DMGNAME}.sha256
cd ..
rm {README,CHANGELOG,COPYING}.txt

if [[ "${APPDMG_EXITSTATUS}" == 0 ]]
then
  echo "The disk image is ready: dist/${DMGNAME}"
  exit 0
fi
