=== LilyPond Documentation ===

Here you can add local paths or remote URLs pointing to LilyPond documentation.

The URLs to the latest stable and development LilyPond manuals are already
set by default for user convenience.

== Local path ==

A local path should point to the directory where either the `Documentation`
directory lives, or the whole `share/doc/lilypond/html/offline-root` path.

If those can't be found, documentation is looked for in all subdirectories
of the given path, one level deep. This makes it possible to put multiple
versions of LilyPond documentation in different subdirectories and have
Frescobaldi automatically find them.

== Remote URL ==

If you don't want to manage the LilyPond documentation locally on your
computer, you can add an URL to the LilyPond website.  The URL should
have the following format:

    http://www.lilypond.org/doc/VERSION/

where *VERSION* can be either a specific release number or the latest stable
or development release, as in the following examples:

    http://www.lilypond.org/doc/v2.18/
    http://www.lilypond.org/doc/v2.19/
    http://www.lilypond.org/doc/stable/
    http://www.lilypond.org/doc/development/
