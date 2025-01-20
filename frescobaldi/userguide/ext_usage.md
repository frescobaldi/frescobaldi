=== Using Extensions ===

Obviously the actual usage of an extension is up to the extension, and so is the
documentation of its features. However, there are some common aspects about the
integration of extensions in the Frescobaldi user interface. Essentially an extension's functionality is available through *Menu Actions* and a *Tool Panel*. At least one of these must exist for any extension.

= Menus =

An extension's *Menu Actions* can be exposed in various {submenu_extensions}
submenus. It is up to the extension maintainer(s) which actions are available in
each of the following places:

* {menu_tools_extensions}
* Editor context menu
* Musicview context menu
* Manuscriptview context menu
* *Additional places may be added over time*

= Tool Panel =

If an extensions provides a Tool Panel it is accessible through {menu_panel}.
The panel behaves like Frescobaldi's built-in dockable panels, and what
functionality it provides is up to the extension.

#VARS

submenu_extensions          menu N.N. -> Extensions
menu_tools_extensions    menu Tools -> Extensions
menu_panel               menu Tools -> Extensions -> [extension-name]
