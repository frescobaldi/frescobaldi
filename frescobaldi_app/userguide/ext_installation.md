=== Installing Extensions ===

In order to use extensions an arbitrary base directory has to be created and
made known to Frescobaldi in {menu_preferences_extensions}, in the first group
“General Settings”. In the same place the check box “Use Extensions” has to be
checked.

Extensions are “installed” by copying the whole extension directory into the
base directory and restarting Frescobaldi. Upon program start Frescobaldi
searches the base directory and loads any compatible extensions automatically.
If an extension is deactivated, only its metadata info is loaded to avoid large
extensions slowing down the startup.

#VARS

menu_preferences_extensions    menu Edit -> Preferences -> Extensions
