=== General Preferences ===

Under *General* preferences, you can choose in which language Frescobaldi's
user interface is translated, which user interface style you want to use, 
and whether you want to use the built-in Tango iconset or to use the 
system-wide configured icon set.

Language and style take effect immediately, but the new iconset is visible
after Frescobaldi has been restarted.

Under *Session to load if Frescobaldi is started without arguments* you can 
configure which session to load if Frescobaldi is started without a 
filename. You can choose whether to start with one empty document, with the 
last used session, or with a specific session. Please note that this only 
works when you have explicitly created a session and set it to automatically 
add files on save to it. See also {sessions}.

Under *When saving documents*, you can choose what to do when a document is 
saved, such as remembering the cursor position and marked lines, formatting,
or leaving a backup copy of the document (with a `~` appended).

Also, you can specify a default folder in which you keep your LilyPond 
documents.

Under *Creating new documents*, you can choose what to do when a new document
is created. It can be left empty (the default), the current LilyPond version
can be set to it, or you can choose any of the templates you defined.

Under *Experimental Features*, you can choose whether to enable features that
are in development and are not yet considered complete.
See {experimental}.

#VARS
sessions help sessions
experimental help experimental_features
