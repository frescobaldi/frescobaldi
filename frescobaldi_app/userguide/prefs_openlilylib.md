=== openLilyLib Preferences

openLilyLib (see [https://github.com/openlilylib](https://github.com/openlilylib))
is a LilyPond package framework giving easy access to custom extension code. It is
supported in Frescobaldi with two goals: offering openLilyLib users a convenient
managing interface and providing additional compilation features in Frescobaldi.
The latter will *not* affect documents themselves (they will remain completely
compatible with other editors).

The “Root directory” is a parent directory where all openLilyLib packages are installed.
If a valid openLilyLib installation directory is selected (this is a directory that
contains at least the `oll-core` package
([https://github.com/openlilylib/oll-core](https://github.com/openlilylib/oll-core)))
a list of installed packages is displayed in the “Installed openLilyLib packages”
panel.

If a root directory is saved it will be implicitly added to LilyPond's include
path when engraving scores. So the openLilyLib root path does *not* have to be
added in the LilyPond Preferences.

*To be continued with implementation.*
