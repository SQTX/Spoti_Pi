
# ****************************************************************
# Imports
# ****************************************************************
import board
import time

import rotaryio # Encoder lib

from digitalio import DigitalInOut, Direction, Pull


# ****************************************************************
# SETTINGS - configuration
# ****************************************************************
'''
-----------------------------------
Pinout:
-----------------------------------
BTN_ex-1        <-> PIN 24 (GP18)
BTN_ex-2        <-> PIN 25 (GP19)
BTN_ex-3        <-> PIN 26 (GP20)
BTN_ex-4        <-> PIN 27 (GP21)
-----------------------------------
SW_encoder      <-> PIN 17 (GP13)
CLK_encoder     <-> PIN 19 (GP14)
DT_encoder      <-> PIN 20 (GP15)
-----------------------------------
'''
# Extension buttons:
btn_like = DigitalInOut(board.GP21)
btn_prev = DigitalInOut(board.GP20)
btn_play = DigitalInOut(board.GP19)
btn_skip = DigitalInOut(board.GP18)
# Encoder:
SW_encoder = DigitalInOut(board.GP13) # Encoder button
CLK_encoder = board.GP14
DT_encoder = board.GP15


# ****************************************************************
# Buttons definitions
# ****************************************************************
buttons = [SW_encoder, btn_like, btn_prev, btn_play, btn_skip]

for btn in buttons:
    btn.direction = Direction.INPUT
    btn.pull = Pull.UP


# ****************************************************************
# Encoder definitions
# ****************************************************************
encoder = rotaryio.IncrementalEncoder(CLK_encoder, DT_encoder)
last_position = None


# ****************************************************************
# Main loop
# ****************************************************************
print("RP Pico is running")

while True:
    enc_position = encoder.position
    if last_position == None or enc_position != last_position:
        print(enc_position)
    last_position = enc_position


    if not buttons[0].value:
        print("BTN_encoder is down")
    elif not buttons[1].value:
        print("BTN_like is down")
    elif not buttons[2].value:
        print("BTN_prev is down")
    elif not buttons[3].value:
        print("BTN_play is down")
    elif not buttons[4].value:
        print("BTN_skip is down")
    else:
        pass


    time.sleep(0.2)
# End of Main loop