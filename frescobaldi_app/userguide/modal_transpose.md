=== Modal transpose ===

Use the modal transpose if you want the notes to be kept within a given scale or key.

Enter the number of steps you want to transpose followed by the given scale.

E.g. when transposing a major second upwards in the key of C major, you would enter:

```lilypond
1 C
```

*Note that if some of the original pitches are outside the given key the relation
will be kept and the pitches will not be adjusted to the key. Hence you can't
use this functionality to shift between different keys. Use the {modeshift} 
function instead.*

#SEEALSO
mode_shift

#VARS
modeshift help mode_shift
