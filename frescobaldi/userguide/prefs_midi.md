=== MIDI Settings ===
    
Here you can configure Frescobaldi's MIDI settings.

You can specify the MIDI port name to play to. If there are no port names 
visible in the drop-down box, it may be necessary to connect a hardware MIDI 
synthesizer to your computer, or to start a software synthesizer program 
such as TiMidity or Fluidsynth.

On Linux, the synthesizer should be available as an ALSA MIDI device.

If you have a device with multiple ports, you can specify the first letters
of the name, to have Frescobaldi automatically pick the first available one.

And finally, when using a software synthesizer it is recommended to enable
the option *Close unused MIDI output*.

If checked, Frescobaldi will close MIDI output ports that are not used for 
one minute. This could free up system resources that a software MIDI 
synthesizer might be using, thus saving battery power. A side effect is that 
if you pause a MIDI file for a long time the instruments are reset to the 
default piano (instrument 0). In that case, playing the file from the 
beginning sets up the instruments again.

