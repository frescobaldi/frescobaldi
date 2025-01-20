=== Extending Frescobaldi ===

Additional functionality can be added Frescobaldi through *Extensions*. These can
be useful for any functionality or tool one might want to work with inside
Frescobaldi but that isn't available or should not be added to the core
application.

Extensions may provide a Tool Panel and menu actions that can be exposed in the
{menu_tools_extensions} and a number of context menus. They have full access to
Frescobaldi's code base and can therefore be very powerful. In particular
extensions may provide

* tools to handle input files or viewer elements
* project management capabilities (librarians, build tools)
* custom editors for various elements (annotations, tweaking tools)
* arbitrary other tools, e.g. an invoice generator, messaging client, Tetris ...

*NOTE:* This power implies risks. An extension may - due to bad programming or
evil intent - do great harm to your whole computer. Please be sure to use
extensions from reliable sources only!

#SUBDOCS
ext_installation
ext_configuration
ext_usage

#VARS

menu_tools_extensions    menu Tools -> Extensions
