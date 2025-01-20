=== Sessions ===

A session is basically a list of open files. At any time you can choose
{menu_session_save} or {menu_session_new} and save the current list of open
files to a named session.

Available sessions are accessible through the {menu_session} menu.
When you switch sessions, all current documents are closed first and then
the documents of the other session are opened.

Inside the session properties dialog, you can specify a default directory for the session.
You can also choose whether to always save
the list of open documents to that session, or to only save on creation (or
via {menu_session_save}). This can be useful if you want to keep the list of
documents in session the same, even if you open or close documents while
working.

Another way of backing up the state of the session is to use the import
and export functionality in the session manager ({menu_session_manage}).
In the session manager you can also add, edit or remove a session.

Sessions can be grouped in the {menu_session} menu by prepending a group name to
the session name, separated by a slash.

#SEEALSO
prefs_general

#VARS
menu_session menu Session
menu_session_new menu session -> New Session|&New...
menu_session_save menu session -> &Save
menu_session_manage menu session -> Manage
