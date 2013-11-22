=== Layout control mode ===

The Layout Control options display or highlight various layout aspects and will
help you fine-tuning your scores.

The options are accessible through the *Layout Control options* dockable panel
({menu_layout_control}).

The following Layout Control options are currently implemented:

Verbose Output
:   Adds the `--verbose` option to the LilyPond commandline, causing LilyPond
    to print lots of information in the log window.
    
Point-and-Click
:   Enables the point and click navigation links in the Music View. Enabled by
    default.

Display Control Points
:   Slurs, Ties and other similar objects are drawn in LilyPond as third-order
    Bezier curves, which means that their shape is controlled by four
    "control-points" (first and last ones tell where the curve ends are placed,
    and the middle ones affect the curvature).
    
    Changing the shape of these objects involves moving these control-points
    around, and it's helpful to see where they actually are.
    
    This option will display the inner control-points as red crosses and
    connects them to the outer (starting) points with thin lines.

Color `\voiceXXX`
:   This mode highlights voices that have been explicitly set with one of the
    `\voiceXXX` commands. This is useful when dealing with polyphony issues.

Color explicit directions
:   This mode colors items whose directions have been explicitly set with either
    the predefined commands `\xxxUp` etc. or the directional operators
    `^` and `_`.
    
    Please note how this mode and the previous are related:
    
    When the condition for one of the the modes is reverted using `\oneVoice`
    or `\stemNeutral`, colors are reverted to black and will also revert the
    highlighting of the other Layout Control mode with LilyPond versions up
    to 2.17.5."
    
    If the score is engraved with LilyPond version 2.17.6 or later this problem
    isn't present anymore.

Display Grob Anchors
:   In LilyPond, all graphical objects have an anchor (a reference point).
    What is a reference point?  It's a special point that defines the object's
    position.
    
    Think about geometry: if you have to define where a figure is placed on a
    plane, you'll usually say something like
    "the lower left corner of this square has coordinates (0, 2)" or
    "the center of this circle is at (-1, 3)".
    
    "Lower left corner" and "center" would be the reference points for square
    and circle.
    
    This Mode displays a red dot for each grob's anchor point.

Display Grob Names
:   This mode prints a grob's name next to it.

    The main purpose of this layout control option is to retrieve information
    about Grob names, which may come in handy if you don't know where to look
    up available properties.
    
    Please note that displaying grob anchors and displaying grob names is
    mutually exclusive because both functions override the grob's stencil.
    
    When both modes are active, only the grob anchors are displayed.
    Please also note that this mode is quite intrusive and may affect the
    layout. It is mainly useful for learning about grob names and will
    especially become usable once it can be activated for single grobs.

Display Skylines
:   LilyPond uses "Skylines" to calculate the vertical dimensions of its
    graphical objects in order to prevent collisions. This mode draws lines
    representing the skylines and is useful when dealing with issues of
    vertical spacing.

Debug Paper Columns
:   LilyPond organises the horizontal spacing in "paper columns".
    This mode prints a lot of spacing information about these entities.

Annotate Spacing
:   LilyPond has a built-in function that prints lots of information about
    distances on the paper, which is very useful when debugging the page layout.

Include Custom File
:   This mode offers the opportunity to add one's own Debug Modes by including
    a custom file. This file will be included at program startup and may contain
    any LilyPond code you would like to have executed whenever you are engraving
    in Layout Control mode.
    
    This file will be parsed before any of the other Layout Control Modes so you
    may use it to configure them.

    The given string will be literally included in an `\include` directive,
    so you are responsible yourself that LilyPond can find it.




#SUBDOCS
engrave_layout_configure

#VARS
menu_layout_control menu tools -> Layout Control &Options
