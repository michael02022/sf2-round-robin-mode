# sf2-round-robin-mode
Round Robin mode for Soundfont 2 files

This is likely a proof-of-concept by me, wondering if it's possible to add round robins in a SF2 file, and the answer is yes!

## REQUERIMENTS
```
pip install python-rtmidi
pip install mido
SF2 player that does not mute notes between control/program changes
```

## HOW TO USE IT
1. Design a SF2 file and JSON file
2. Check the name of your midi inputs/outputs
3. Set your midi controller/MIDI input, your SF2 Player/MIDI output and your JSON file with editing the .py file
4. Load the SF2 in your player, run the python file and start playing!

## HOW TO CREATE A JSON FILE
You need a text editor, I recommend Notepad++

Then you can load the blank.json file template, remember to use valid JSON syntax.

* "kits" is a JSON array for midi channel 10
* "program" is for the preset number the user must select to trigger the round robin mechanism
* "p_list" is the list of preset/program change values that automatically will be selected in every note


* "presets" is a JSON array for the rest of midi channels
* "program" and "msb" are the program change and control change MSB bank values the user must select to trigger the round robin mechanism
* "msb_list" is the list of control change MSB bank values that automatically will be selected in every note


You can create many objects you want on "kits" and "presets", check the "rrdemo" files for better understanding
