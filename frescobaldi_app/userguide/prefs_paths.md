=== Paths ===

== Hyphenation dictionaries ==

Here, directories can be added that contain `hyph_*.dic` files,
where the `*` stands for different language codes.

These hyphenation dictionaries are used by Frescobaldi to break
lyrics text into syllables.

== Music fonts ==

Since version 2.19.12 LilyPond natively supports the selection of
alternative music fonts, and Frescobaldi supports both the management
of their installation (they have to be installed in each LilyPond version)
and generating the command to choose a set of fonts in a document.

* *Music Font Repository:* Typically one will want to store music fonts
  in a dedicated directory. If this directory is selected here the
  Document Fonts dialog can easily install the fonts in the "current"
  LilyPond installation.
* *Auto Install:* If this box is checked fonts are installed into the
  current LilyPond installation whenever the Document Fonts dialog is
  opened. With this option checked the user doesn't really have to think
  about the need to install the music fonts in each new LilyPond
  installation.
* *Music Font Preview Cache:* The Document Fonts dialog compiles and displays
  preview samples using the selected music and text fonts. In order to
  provide a seamless user experience these samples are cached, so if
  a combination of content and fonts has already been compiled the
  resulting scores can simply be swapped.  By default caching is only
  done within the current Frescobaldi session because the temporary
  directories are cleaned up after the program terminates.  If a
  writable directory is set here the sample scores provided by Frescobaldi
  are cached persistently.
