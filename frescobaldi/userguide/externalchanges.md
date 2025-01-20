=== Monitoring external changes ===

Frescobaldi can detect if files are modified or deleted by other applications.

When another application modifies or deletes one or more documents that are 
opened in Frescobaldi, a list of affected documents is displayed, and you 
can choose whether to reload one or more documents from disk, or to save 
them, discarding the modifications made by the other application.

When a document is reloaded, you can still press {key_undo} to get back the 
document as it was in memory before reloading it from disk.

Press the *Show Difference...* button to see the difference between 
the current document and its version on disk.

If you don't want to be warned when a document is changed or deleted by 
another application, uncheck the *Enable watching documents for external 
changes* checkbox.


#VARS
key_undo shortcut main edit_undo
