#
# Created by Jakub SQTX Sitarczyk on 27/02/2024.
#
# ****************************************************************
# Imports
# ****************************************************************
# Control
import board
import time
import rotaryio # Encoder lib
from digitalio import DigitalInOut, Direction, Pull
# Server
import os
import socketpool
import wifi
import ipaddress
import adafruit_requests, ssl
from adafruit_httpserver import Server, Request, Response, FileResponse, GET


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
# Server
# SPDX-FileCopyrightText: 2022 Dan Halbert for Adafruit Industries
# ****************************************************************
ssid = os.getenv("WIFI_SSID")
password = os.getenv("WIFI_PASSWORD")


print("Connecting to", ssid)
wifi.radio.connect(ssid, password)
print("Connected to", ssid)

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())    # HTTP requests
server = Server(pool, "/static", debug=True)


# ****************************************************************
# Routing
# ****************************************************************
@server.route("/")
def base(request: Request):
    """
    Starting website with link to another subsite
    """
    return FileResponse(request, "index.html", "/public")


@server.route('/test')
def test(request: Request):
    """
    Test subsite
    """
    return Response(request, "TESTer Skura")


# ****************************************************************
# Main APP
# ****************************************************************
print("RP Pico is running")

server.serve_forever(str(wifi.radio.ipv4_address)) # Start local server


# Main loop
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