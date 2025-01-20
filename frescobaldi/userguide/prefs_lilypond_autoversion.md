=== Automatically choose LilyPond version from document ===
    
If this setting is enabled, the document is searched for a
LilyPond `\version` command or a `version` document variable.

The LilyPond version command looks like:

```lilypond
\version "2.14.0"
```

The document variable looks like:

```
-*- version: 2.14.0;
```

somewhere (in a comments section) in the first or last 5 lines of the document.
This way the LilyPond version to use can also be specified in non-LilyPond
documents like HTML, LaTeX, etc.

If the document specifies a version, the oldest suitable LilyPond version
is chosen. Otherwise, the default version is chosen.


#SEEALSO
docvars
