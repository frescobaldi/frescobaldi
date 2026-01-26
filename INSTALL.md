# Installation instructions for Frescobaldi


## Using a pre-built package

Each release comes with installers for Windows and macOS.  These are available
from

https://github.com/frescobaldi/frescobaldi/releases/

This is the simplest way of installing Frescobaldi under Windows or macOS.

Under Linux, your distribution probably provides a `frescobaldi` package.  If
so, installing it is the easiest route, even though it might be out of date.
Run `sudo apt install frescobaldi` on Debian/Ubuntu or `sudo dnf install
frescobaldi` on Fedora.

You can also install [Frescobaldi from Flathub](https://flathub.org/apps/org.frescobaldi.Frescobaldi) using Flatpak to get a more up-to-date application:

```
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install flathub org.frescobaldi.Frescobaldi
flatpak run org.frescobaldi.Frescobaldi
```

If you previously installed Frescobaldi via your distribution, remember to
remove it before installing it through Flatpak. Otherwise, they will coexist on
your computer; while this is not a problem per se, you could get the old
Frescobaldi version when you launch Frescobaldi graphically.

If you are *not* a developer and none of the options above are right for you, then install the compressed tar file (.tar.gz) using the instructions below.

### Installing the compressed tar file

It is a good idea to uninstall any previous versions before continuing.  See [Uninstalling other versions](#uninstalling-other-versions) for how to do this.

#### Download, extract and move the Frescobaldi directory

If you have not already done so, go to the [latest release page](https://github.com/frescobaldi/frescobaldi/releases/latest) and download the compressed tar file called `frescobaldi-x.y.z.tar.gz` (where `x`, `y`, and `z` are the version numbers), and extract the files from it.  You may be able to do this using GUI tools.  Your browser may extract the files when you click on the downloaded file, or using whatever File Manager you have, try double-clicking or right-clicking.  There are also third-party apps that will extract compressed files.

Move the extracted directory to a permanent location, like your home directory.  (The rest of the instructions will assume that the extracted files are in the home directory.)

If you can't extract the file using GUI tools, you can use the command line.  Get to a command prompt and `cd` to your Download directory.  This is often in your home directory, which you can get to by typing `cd` by itself.  Once in the download directory, use `ls` to make sure you have this file:

    frescobaldi-x.y.z.tar.gz

To extract the file, type

    tar xvf frescobaldi-x.y.z.tar.gz

You should now have the directory `frescobaldi-x.y.z` in your download directory.  Move it to your home directory by typing

    mv frescobaldi-x.y.z ~

#### Install the necessary tools

At this point, if you have been using GUI tools, you will need to get to the command line.  We will now install some tools needed to install Frescobaldi.  You only have to do this once.  The next release you install, you can skip this.  If you are on a Debian/Ubuntu-like distribution, type:

    sudo apt install pipx gettext libportmidi0 libxcb-cursor0

If you are on Fedora, type:

    sudo dnf install pipx gettext portmidi

#### Install using `pipx`

At the command line, type:

    cd ~/frescobaldi-x.y.z
    pipx install .

After a few moments, `pipx` will say Frescobaldi is installed.  Next, install the desktop shortcut (this is all one command):

    desktop-file-install --dir ~/.local/share/applications/ --set-icon $PWD/frescobaldi/icons/org.frescobaldi.Frescobaldi.svg  linux/org.frescobaldi.Frescobaldi.desktop

Now update the desktop database:

    update-desktop-database ~/.local/share/

 If this is your first time installing using `pipx`, type the following:

    pipx ensurepath

Then type `exit` and restart your command line shell.  Now you can to type:

    frescobaldi

...and Frescobaldi will start up.

## Developing Frescobaldi

If you would like to help with the development of Frescobaldi, a Linux platform
is recommended. You will need install it from source in editable
mode. Frescobaldi is closely tied to two companion modules, python-ly and
qpageview; you might want to modify these too, so it is recommended to install
them from source as well.

### Uninstalling other versions

While not required, it is a good idea to save yourself confusion in the future
by uninstalling other versions of Frescobaldi. For example, `sudo apt remove
frescobaldi` if you installed via the system package on Debian/Ubuntu, `sudo dnf
remove frescobaldi` on Fedora, or `flatpak remove org.frescobaldi.Frescobaldi`
if you installed it via Flatpak, or `pip uninstall frescobaldi python-ly
qpageview` if you used pip, or `pipx uninstall frescobaldi` if you used pipx.

### Getting basic requirements

Frescobaldi is written in Python 3, so you will need a Python interpreter.  Most
Linux distributions come with Python 3 preinstalled.  Make sure that `python
--version` works.

You will also need a few packages from your operating system:

* [pipx](https://pypa.github.io/pipx), for the installation process,
* [tox](https://tox.wiki), for orchestrating the build of autogenerated files,
* Git, the version control software used for Frescobaldi's source code,
* GNU Gettext, a suite of tools for working with translations, for generating
  compiled MO catalogs.
* [PortMidi](https://github.com/PortMidi/portmidi), for MIDI playback.

On Debian/Ubuntu, these packages can be installed using:

```
sudo apt install pipx tox git gettext libportmidi0
```

On Fedora:

```
sudo dnf install pipx tox git gettext portmidi
```

PyQt6 dependencies will be automatically installed from PyPI
when you install Frescobaldi.


### Getting the source code

Create a directory where you will store the Frescobaldi sources and
`cd` into it.  For example:

```
mkdir frescobaldi-repositories
cd frescobaldi-repositories
```

Next, clone the repository:

```
git clone https://github.com/frescobaldi/frescobaldi.git
```

### Creating autogenerated files

The following commands generate `.mo` files for translations, and a desktop
file.

```
cd frescobaldi
tox -e mo-generate
tox -e linux-generate
cd ..
```

### Installing Frescobaldi

Install from source with `pipx`:

```
pipx install --editable ./frescobaldi
```

The `--editable` option makes sure that your changes to the source code will be
reflected.

pipx will install also the dependencies listed in `pyproject.toml`.
You can see the installed packages in
`~/.local/share/pipx/venvs/frescobaldi/lib/python3.XY/site-packages`.

After this command, you should be able to run Frescobaldi from source by running
`frescobaldi`.

### Installing the desktop file

The desktop file is what enabled you to run Frescobaldi as a normal application,
by clicking on an icon, instead of running Frescobaldi in a terminal. Install it
using

```
cd frescobaldi
desktop-file-install --dir ~/.local/share/applications/ --set-icon $PWD/frescobaldi/icons/org.frescobaldi.Frescobaldi.svg  linux/org.frescobaldi.Frescobaldi.desktop
update-desktop-database ~/.local/share/
cd ..
```

After waiting a few seconds, you should find a Frescobaldi application on your
system.

### Optional: installing python-ly and qpageview as editable

You now have a copy of Frescobaldi's source code that you can edit and launch
easily. However, Frescobaldi relies on two companion modules, python-ly and
qpageview, which you may want to develop as well. If you want to be able to
develop them, clone their sources:

```
git clone https://github.com/frescobaldi/python-ly.git
git clone https://github.com/frescobaldi/qpageview.git
```

then "inject" them into the already installed application so that they replace
the automatically downloaded copies of python-ly and qpageview:

```
pipx inject --editable frescobaldi ./python-ly ./qpageview
```

### Optional: additional features

Finally, you may want to install some optional modules that are needed
for certain features.

* If you want to print PDFs to a local CUPS server, also install `pycups` using
  `pipx inject frescobaldi pycups`. This [may require](https://gitmemories.com/index.php/OpenPrinting/pycups/issues/50)
  `sudo apt install libcups2-dev`
  in order to work properly.


## For Linux distribution packagers

See above for the dependencies that need to be installed.

Please note that a few files should be manually copied to the
proper system directories for the installation to work correctly:

| File type | File name                       | Installation directory |
| --------- | ------------------------------- | ---------------------- |
| Icon      | org.frescobaldi.Frescobaldi.svg | /usr/share/icons/hicolor/scalable/apps |
| Desktop   | org.frescobaldi.Frescobaldi.desktop | /usr/share/applications |
| Metainfo  | org.frescobaldi.Frescobaldi.metainfo.xml | /usr/share/metainfo |

Frescobaldi contains some files by default which are also available in other
packages often used in Linux distributions. It is possible to remove those
files after installing/packaging and make Frescobaldi depend on the package
containing those files. This makes the filesystem less cluttered, and copyright
files simpler.

Icons:
You can remove the frescobaldi/icons/Tango directory, and make Frescobaldi
depend on the tango-icon-theme package instead.

Hyphenation dictionaries:
You can remove the hyph_*.dic files from frescobaldi/hyphdicts, and make
Frescobaldi depend on a package that installs hyphenation dictionaries in
/usr/share/hyphen/ (or another dictionary listed by default in frescobaldi/
hyphendialog.py). Do not remove the hyphdicts directory entirely.
