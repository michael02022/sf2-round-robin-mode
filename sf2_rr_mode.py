import json
import sys

import mido

YOUR_MIDI_IN_PORT = "MIDI Controller 1"
YOUR_MIDI_OUT_PORT = "SF2plugin 2"
YOUR_JSON_FILE = "rrdemo.json"

# pause the program if there's an error
def show_exception_and_exit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input("Please read the error, press key to exit.")
    sys.exit(-1)

sys.excepthook = show_exception_and_exit

# round robin algorithm
n = -1

def round_robin(seq):
    global n
    n = n + 1
    n = seq[n % len(seq)]
    return n

# convert list into index list
def get_indexes(list):
    newlist = []
    for i in range(len(list)):
        newlist.append(i)
    return newlist

# process midi message to change the MSB value on every note on
def preset_rr(msg, list, program_pc):
    msgtype = msg.type
    msgchan = msg.channel
    msgnote = msg.note
    msgvel = msg.velocity

    if msgtype == "note_off" or msgvel == 0:
        return [msg] # returns note off
    else:
        # round robin
        indexes = get_indexes(list) # get the indexes as list
        idx = round_robin(indexes) # set the index based on round robin result
        return [mido.Message("control_change", channel=msgchan, control=0, value=list[idx]), # set the MSB
        mido.Message("control_change", channel=msgchan, control=32, value=0),
        mido.Message("program_change", channel=msgchan, program=program_pc), # send all necessary midi messages
        mido.Message(msgtype, channel=msgchan, note=msgnote, velocity=msgvel)] #send note

def kits_rr(msg, list):
    msgtype = msg.type
    msgchan = msg.channel
    msgnote = msg.note
    msgvel = msg.velocity

    if msgtype == "note_off" or msgvel == 0:
        return [mido.Message(msgtype, channel=msgchan, note=msgnote, velocity=msgvel)]
    else:
        # round robin
        indexes = get_indexes(list) # get the indexes as list
        idx = round_robin(indexes) # set the index based on round robins
        return [mido.Message("control_change", channel=msgchan, control=0, value=0),
        mido.Message("control_change", channel=msgchan, control=32, value=0),
        mido.Message("program_change", channel=msgchan, program=list[idx]), # set program change
        mido.Message(msgtype, channel=msgchan, note=msgnote, velocity=msgvel)]

# initialise values
json_kits = list(range(128)) # all 127 pc values for kits, we'll inject the round robin lists to the correct indexes
json_kits_pc = [] # list with all kits with round robins

json_presets = list(range(128)) # all preset values, we'll inject the round robin lists to the correct indexes
json_program_rr = [] # lists all programs with rr
json_msb_rr = [] # lists all MSB with rr (combo with program)

current_msb = 0
current_lsb = 0
current_pc = 0
chan_pc_lst = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # midi channels pc list
chan_msb_lst = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # midi channels msb list

def load_json_arrays(jsonf):
    with open(jsonf, "r") as f:
        obj = json.loads(f.read())
        for j in obj["kits"]:
            json_kits_pc.append(j["program"]) # documents the kits that has round robins
            json_kits[j["program"]] = j["p_list"] # replace index with the array of round robins
        for i in obj["presets"]:
            json_program_rr.append(i["program"]) # documents the presets that has round robins
            json_msb_rr.append(i["msb"]) # documents the lsb combination that has round robins
            json_presets[i["program"]] = i["msb_list"] # replace index with the array of round robins

def process_msg_inst(msg, msb, pc):
    # if the current selected program is on the list of documented rr presets combinations
    if pc in json_program_rr and msb in json_msb_rr:
        msbarray = json_presets[pc] # get the array of rr from json
        msblist = preset_rr(msg, msbarray, pc) # process the midi message and returns a list where includes the MSB changes
        for i in range(len(msblist)):
            outport.send(msblist[i]) # send every message from list in order
            # print(msblist[i])
    else:
        outport.send(msg)
        # print(msg)

def process_msg_kit(msg, pc):
    if pc in json_kits_pc:
        kitsarray = json_kits[pc] # get the array of rr from json
        kitslist = kits_rr(msg, kitsarray) # same as preset_rr but only for program change
        for i in range(len(kitslist)):
            outport.send(kitslist[i])
            # print(kitslist[i])
    else:
        outport.send(message)
        # print(message)

# PRINT INPUT/OUTPUT MIDI PORTS 
print("MIDI INPUTS", mido.get_input_names())
print("MIDI OUTPUTS", mido.get_output_names())

# LOADS JSON FILE
load_json_arrays(YOUR_JSON_FILE)

# SELECT THEM
inport = mido.open_input(YOUR_MIDI_IN_PORT)
outport = mido.open_output(YOUR_MIDI_OUT_PORT)

# STARTS LISTENING TO MIDI MESSAGES
print("Ready!")
with inport:
    for message in inport:
        if hasattr(message, "control"): # if its CC
            if (message.control == 121):
                outport.send(message) # send the message without any processing
            elif (message.control == 123):
                outport.send(message)
            elif (message.control == 0):
                current_msb = message.value # updates the current values
                chan_msb_lst[message.channel] = current_msb # set the value to the channel
                outport.send(message)
            elif (message.control == 32):
                current_lsb = message.value # updates the current values
                outport.send(message)
            else:
                outport.send(message) # send the rest of unlisted CC
        elif hasattr(message, "pitch"): # if its pitch
            outport.send(message) # send it
        elif hasattr(message, "program"): # if its program change
            current_pc = message.program # updates the current values
            chan_pc_lst[message.channel] = current_pc # set the value to the channel
            outport.send(message) # send it
        elif hasattr(message, "sysex"):
            outport.send(message) # send it
        else:
            if (message.channel != 9):
                process_msg_inst(message, chan_msb_lst[message.channel], chan_pc_lst[message.channel])
            else:
                process_msg_kit(message, chan_pc_lst[message.channel])
