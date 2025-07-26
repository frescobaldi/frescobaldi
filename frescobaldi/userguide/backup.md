=== Backup ===

All the application settings (paths to LilyPond installations, custom snippets, MIDI ports and any other preferences) are saved in the main configuration file.

If you want to backup your settings or use them in another computer, you must know where to find it. The file format and location depends on the operating system default.


== Linux ==

On Linux the settings file is a plain text file in the INI format.
For regular installations the path is `~/.config/frescobaldi/frescobaldi.conf`; for Flatpak installations it's `~/.var/app/org.frescobaldi.Frescobaldi/config/frescobaldi/frescobaldi.conf`.


== macOS ==

On macOS the settings file is a Apple binary property list located at `/Library/Preferences/org.frescobaldi.frescobaldi.plist`.

If you want to share the contents with others (for example to help a developer to debug an issue), you should first convert it to a plain XML file:

```
cd /Library/Preferences
plutil -convert xml1 -o org.frescobaldi.frescobaldi.xml.plist org.frescobaldi.frescobaldi.plist
```


== Windows ==

On Windows the settings are saved in the following registry path: `HHKEY_CURRENT_USER\software\Frescobaldi\frescobaldi`.

You can use the Registry Editor to check or backup your settings.


#SEEALSO
snippet_import_export
