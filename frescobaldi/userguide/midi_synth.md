=== Playing a MIDI file does not work ===
    
The built-in MIDI player needs an external synthesizer to make the MIDI 
audible, otherwise it will play the file silently, only showing the "No 
Output Found!" message.

So make sure either a software synthesizer like TiMidity or FluidSynth is 
running (preferably at bootup or session login), or you have an external 
MIDI synthesizer connected to your computer.

In the {midi_prefs} you can configure which MIDI port you want to use for 
playing the MIDI files.

#VARS
midi_prefs help prefs_midi
