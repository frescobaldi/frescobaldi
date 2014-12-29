=== Modal transpose ===

Use the modal transpose if you want the notes to be kept within a given scale or key.

Enter the number of steps you want to transpose followed by the given scale.

E.g. when transposing a major second upwards in the key of C major, you would enter:

```lilypond
1 C
```

Note that if some of the original pitches are outside the given key the relation
will be kept and the pitches will not be adjusted to the key. Hence you can't
use this functionality to shift between different keys. 

But a special trick would be to use modal transpose and (chromatic) transpose in combination: 
You would then make use of the fact that different modes have the same set of pitches. 
If we take the example above which moves the music upwards a major second in the key of C major, 
and then use the regular non-modal transpose `d c` to move the music downwards to its 
original position; we have in effect shifted the music from C major to C dorian.

