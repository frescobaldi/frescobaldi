=== Configuring the Layout Control options ===

The appearance of the individual Layout Control modes is defined through
the use of configuration variables.

Depending on the implementation the mode you may modify its appearance by
redefining these variables in your input files.

But if you are interested in a more general solution you can make use of the
"Custom file" mode.
As this custom file is read in before the different layout control modes you can
use it to define any of the variables *before* the layout control modes are
parsed.

The modes use the following configuration variables:


Display Control Points
:   These variables can be redefined in input files:
    
    * !`debug-control-points-color` (`red`)
    * !`debug-control-points-line-thickness` (`0.05`)
    * !`debug-control-points-cross-thickness` (`0.1`)
    * !`debug-control-points-cross-size` (`0.7`)


Color \voiceXXX
:   These variables currently can't be redefined in input files.

    * !`debug-voice-one-color` (`darkred`)
    * !`debug-voice-two-color` (`darkblue`)
    * !`debug-voice-three-color` (`darkgreen`)
    * !`debug-voice-four-color` (`darkmagenta`)


Color explicit directions
:   These variables can be redefined in input files:
    
    * !`debug-direction-up-color` (`blue`)
    * !`debug-direction-down-color` (`blue`)
    * !`debug-direction-grob-list` (`all-grob-descriptions`)
    
        Defines for which grobs the explicit direction through operators is
        monitored.
        By default all grobs are watched, but alternatively one can provide a
        list of grobs such as e.g.
        
        ```lilypond
#(define debug-direction-grob-list '(DynamicText Script))
```
        

Display Grob Anchors
:   These variables can be redefined in input files:

    * !`debug-grob-anchors-dotcolor` (`red`)
    * !`debug-grob-anchors-grob-list` (`all-grob-descriptions`)
    
        Defines for which grobs the anchor points will be displayed.
        By default all grobs are watched, but alternatively one can provide a
        list of grobs such as e.g.
        
        ```lilypond
#(define debug-grob-anchors-grob-list '(Script NoteHead))
```
        

Display Grob Names
:   These variables can be redefined in input files:

    * !`debug-grob-names-color` (`darkcyan`)
    * !`debug-grob-names-grob-list` (`all-grob-descriptions`)
    
        Defines for which grobs the names will be displayed.
        By default all grobs are watched, but alternatively one can provide a
        list of grobs such as e.g. 
        
        ```lilypond
#(define debug-grob-names-grob-list '(Script NoteHead))
```

The remaining modes are built-in to LilyPond and don't have any configuration
options.

