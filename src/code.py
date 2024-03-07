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
from circuitpython_parse import urlencode


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
# Spotify API const
# ****************************************************************
# User data:
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")    # URL/IP+/callback
# ---------------------------------------------------
# Url addresses:
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"


# ****************************************************************
# SoftRAM
# ****************************************************************
'''
access_token = ""
refresh_token = ""
expires_at = 0
'''
session = []

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


@server.route('/login')
def login(request: Request):
    scope = "user-read-private user-read-email playlist-read-private user-read-currently-playing user-modify-playback-state"

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    return Redirect(request, auth_url)


@server.route('/callback')
def callback(request: Request):
    if 'error' in request.query_params.fields:
        #return JSONResponse(request, {"error": request.query_params.get('error')})
        return Response(request, "Error")

    if 'code' in request.query_params.fields:
        req_body = {
            "code": request.query_params.get('code'),
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        try:
            response = requests.post(TOKEN_URL, data=req_body)
            token_info = response.json()
            response.close()

            print(token_info)

            #global access_token, refresh_token, expires_at  # Define variables like a global var

            session.append(token_info['access_token'])
            session.append(token_info['refresh_token'])
            expires_at = time.time() + token_info['expires_in']
            session.append(expires_at)

        except Exception as e:
            print("Error-callback:\n", str(e))

        return Redirect(request, "/main")


@server.route('/main')
def main(request: Request):
    access_token = session[0]
    expires_at = session[2]

    if access_token == "":
        return Redirect(request, "/login")
    if time.time() > expires_at:
        return Redirect(request, "/refresh")

    try:
        req_url = API_BASE_URL + "me/player/currently-playing"

        req_headers = {'Authorization': f"Bearer {access_token}"}

        response = requests.get(req_url, headers=req_headers)   # ERROR
        curr_playing = response.json()
        response.close()

    except Exception as e:
        print("Error-main:\n", str(e))

    # TODO: If img's not exist
    #img_url = playlists['item']['album']['images'][1]['url']
    #print(img_url)

    return FileResponse(request, "main.html", "/public")


@server.route('/skip')
def skip(request: Request):
    if access_token == "":
        return Redirect(request, "/login")

    if time.time() > expires_at:
        return Redirect(request, "/refresh")

    try:
        req_url = API_BASE_URL + "me/player/next"
        req_headers = {'Authorization': f"Bearer {access_token}"}

        requests.post(req_url, headers=req_headers)

    except Exception as e:
        print("Error-skip:\n", str(e))

    return Redirect(request, "/main")


@server.route('/refresh')
def refresh():
    if access_token == "":
        return Redirect(request, "/login")

    if time.time() > expires_at:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        try:
            response = requests.post(TOKEN_URL, data=req_body)
            new_token_info = json.loads(response.text)

            access_token = new_token_info['access_token']
            expires_at = time.time() + new_token_info['expires_in']

            return Redirect(request, "/main")
        except Exception as e:
            print("Error-refresh:\n", str(e))


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