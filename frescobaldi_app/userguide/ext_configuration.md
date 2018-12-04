l=== Configuring Extensions ===

{menu_preferences_extensions} provides an interface to configuring extensions,
globally and per extension. Note that most changes done here require a restart
of Frescobaldi to take effect.

= General Settings

The use of extensions can be deactivated globally. Without this checkbox checked
only the extensions' meta information is accessed and no extension code loaded.

Setting the path to a common extension base directory is the most important step
to get extensions running. However, selecting an arbitrary existing directory
should do no harm as only valid and functional extensions are loaded.

= Installed Extensions

This tree view lists all installed (i.e. found) extensions, regardless whether
they are loaded or not. Expanding an entry displays a list with useful meta
information on the extension.

The checkbox beside the extension name indicates whether an extension is active
or not. Newly detected extensions are by default active. Unchecking or checking
this checkbox manually activates or deactivates the extension.

Selecting an extension will reveal a configuration area in the lower part of the
page if the extension provides it. *Note*: The availability and implementation
of extension configuration is completely in the responsibility of the extension
maintainer(s).

If the *API version* entry does not match Frescobaldi's extension API version
its entry will be highlighted and point to the difference. Such a version
mismatch is not *generally* considered to be an error, but it *can* cause
problems, and this information will be helpful tracking down the problem.

= Failed Extensions =

Extensions can be faulty so that either the meta information can not be parsed
properly or they cause errors upon loading. If either is the case an additional
tree view is displayed with details about the issue.

In a first sublist extensions are listed that have faulty meta information. The
extensions are loaded anyway, but proper functioning can not be guaranteed.
Details are shown to give an indication of the source of the problem.

A second sublist shows extensions that could not be loaded properly. The detail
entry gives a short description of the problem as reported by Python. Double
clicking on the details row opens a message box with more details about the
issue, including the full stacktrace that can (and should) be sent to the
extension maintainer(s) to investigate the issue.

= Extension Configuration =

Extensions can provide a configuration interface, which - if present - will be
displayed as the last group on the Preferences page. *Note*: For technical
reasons it is not possible to edit the configuration of deactivated extensions.

#VARS

menu_preferences_extensions    menu Edit -> Preferences -> Extensions
