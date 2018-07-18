=== Version Control ===

Frescobaldi offers experimental support for version control in documents, which
is currently limited to *Git* repositories and very limited in scope. The
functionality described below is available when experimental features have been
activated in the Preferences *and* Git is installed on the system and can be
found (see also [prefs_helpers "Helper Applications"]).

Whenever a document is loaded that is tracked in a repository symbols in an
additional column next to the line numbers will indicate added (green),
modified (orange) or deleted (red) lines:

{image_vcs_sidebar}

Double-clicking on an indicator will open a pop-up window showing a detailed
diff of the (contigious) modification and a button that will revert this
section to the unmodified state.

== Limitations

Due to the experimental state of version control support there are *substantial*
limitations to the functionality, the most important being

* The base for the comparison is always the committed state of the file.
  Staged files or the “staged modified” state are not considered yet. So it is
  not possible to revert to the staged state or to unstage hunks.
* Modifications are always calculated to the current state of the document
  *as seen in the editor* (that is, not as saved on disk).
* Reverting a hunk will modify the document *in the editor* to match the hunk
  in the committed state. The document will not be saved automatically. *NOTE:*
  this may produce unexpected results when reverting lines that have already been
  staged externally (when saving the file Git will see the result as
  *staged modified* and not as *unmodified*). See also
  [https://github.com/wbsoft/frescobaldi/issues/1001] for further discussion.

* Reverting a hunk will confuse the *undo* stack, so using `Ctrl+Z` after
  reverting will seemingly mess up the lines in many cases. If this happens the
  state before the revert can be reached by applying *undo* a second time.
  See [https://github.com/wbsoft/frescobaldi/issues/1002] for further discussion
  and to check if the bug is still present.
* The *stage*, *unstage*, and *commit* operations have not been implemented yet.

Further limitations and feature requests can be seen and added on
[https://github.com/wbsoft/frescobaldi/labels/git-development this] selection
of the issue tracker.

Another list of known issues is 
[https://github.com/wbsoft/frescobaldi/labels/gsoc-2017-git this] selection of
the issue tracker.


#VARS

image_vcs_sidebar image vcs_sidebar.png
