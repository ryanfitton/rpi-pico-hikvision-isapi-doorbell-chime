# coding: utf-8
# CircuitPython Libaries:
#import network                          #CircuitPython default lib - WiFi on built in model not yet supported
#import adafruit_requests as requests    #From `adafruit_requests.py` lib on local file system
#import json                             #CircuitPython default lib
#import random                           #CircuitPython default lib
#import  re                              #CircuitPython default lib
#import binascii                         #CircuitPython default lib
#from binascii import a2b_base64         #Decode - CircuitPython default lib
#from binascii import b2a_base64         #Encode - CircuitPython default lib

#MicroPython Libaries
import network                          #Micropython default lib
import urequests as requests            #Micropython default lib
import ujson as json                    #Micropython default lib
import urandom as random                #Micropython default lib
import ure as re                        #Micropython default lib
import ubinascii                        #Micropython default lib
from ubinascii import a2b_base64        #Decode - Micropython default lib
from ubinascii import b2a_base64        #Encode - Micropython default lib
#import uhashlib as hashlib             #From `lib/uhashlib.py` lib on local file system - Not required
import time                             #Micropython default lib
import md5                              #From `lib/md5.py` lib on local file system
import os                               #Micropython default lib
from machine import I2S                 #Micropython default lib
from machine import Pin                 #Micropython default lib
import gc                               #Micropython default lib



######################################################
# Notes
######################################################
# Made with help from these pages:
#
#   https://tpp.hikvision.com/Wiki/ISAPI/Access%20Control%20on%20Person/GUID-A4CD59AB-948B-4C20-AE5D-E2F44DE3618E.html
#   https://forum.arduino.cc/t/solved-digest-authentication-on-mkr-wifi-1010-esp32/589750/2
#   https://github.com/SpotlightKid/mrequests
#   https://github.com/lemariva/ESP32MicroPython/blame/master/md5.py
#   https://medium.com/@jamesemyn/deep-dive-in-http-authentication-7565d677adbd
#   https://github.com/hnimminh/http-authentication/blob/master/client.py
#   https://learn.adafruit.com/circuitpython-libraries-on-micropython-using-the-raspberry-pi-pico
#   https://github.com/miketeachman/micropython-i2s-examples



######################################################
# Config
######################################################
#WiFi Configuration
ssid = ""                                           #WiFi network name
ssid_password = ""                                  #WiFi network password

#Doorbell API Configuration
api_username="admin"                                #Doorbell Admin user
api_password=""                                     #Doorbell Admin user's password
host="http://xx.xx.xx.xx"                           #The Doorbell - Highly recommended to setup static DHCP mappings for this device on your router
api_base="/ISAPI/VideoIntercom/"                    #URL Base for Doorbell API

#WAV Audio File Configuration
#8000Hz, 16-Bit PCM
wifi_connected_sound="wifi-connected.wav"

#doorbell_sound="doorbell.wav"
#doorbell_sound="doorbell-loud.wav"
#doorbell_sound="doorbell-new-quiet.wav"
#doorbell_sound="doorbell-new-mid.wav"
doorbell_sound="doorbell-new-loud.wav"
#doorbell_sound="doorbell-new-louder.wav"

wav_file_sample_size_in_bits = 16
wav_file_format = I2S.STEREO
sample_rate_in_hz = 8000

#I2S Sound Board Configuration
#Based on Git repo here: https://github.com/miketeachman/micropython-i2s-examples
#Based on: MAX98357A (https://shop.pimoroni.com/products/adafruit-i2s-3w-class-d-amplifier-breakout-max98357a?variant=21696217799)
#And: https://www.recantha.co.uk/blog/?p=20950
#LRC to Pico GP11
#BLCK to Pico GP10
#DIN to Pico GP9
#GND to Pico 38 (GND)
#VIN to Pico 36 (3V3 OUT)
I2S_sck_pin = 10    #Serial clock output
I2S_ws_pin = 11     #Word clock output
I2S_sd_pin = 9      #Serial data output
I2S_id = 0
I2S_buffer_length_in_bytes = 5000



######################################################
# Functions
######################################################

# Initialise WiFi
# =====================================================
def initWiFi():
 wlan = network.WLAN(network.STA_IF)    # Create an object
 wlan.active(True)                    # Turn on the Raspberry Pi Pico W’s Wi-Fi
 wlan.connect(ssid, ssid_password)    # Connect to your router using the SSID and PASSWORD
 
 # Wait for connection or failure
 max_wait = 10
 while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1

    #Debugging
    logger('Connecting to WiFi...')

    time.sleep(1)
 
 # Handle connection errors
 if wlan.status() != 3:
    raise Exception('Network connection failed')

    return False

 # If connected
 else:
    #Debugging
    logger('WiFi is connected')
    
    #Get status of WiFi
    status = wlan.ifconfig()
    
    #Play sound to notify wifi is connected
    #Disabled as this will play if the WiFi has dropped and re-connected often
    #playSound(wifi_connected_sound)

    #Debugging
    logger('IP Address: ' + status[0])
    
    return True


# Message logger - Mainly for debugging
# =====================================================
def logger(message):
    print(message)


# Authorisation Classes and Functions 
# Code from: https://github.com/hnimminh/http-authentication/blob/master/client.py
# Code on Github is licensed under MIT (https://github.com/hnimminh/http-authentication/blob/master/LICENSE)
# =====================================================
def parse_scheme(_challenge):
    scheme_pattern = _challenge.split(" ") #Split by space and return first item, should be 'digest' or 'basic'
    return scheme_pattern[0]

def gen_basic_credential(username, password):
    #return 'Basic {}'.format(base64.b64encode(username + ':' + password))
    return 'Basic {}'.format(ubinascii.b2a_base64(username + ':' + password).decode('utf-8')) #Optmised for MicroPython

class DigestAuthorization:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.txnids = {}

    @staticmethod
    def _parse_challenge(_challenge):
        _challenge = _challenge.strip('Digest ').split(', ')
        digest_challenge_pattern = {}
        for value in _challenge:
            value = value.replace('"', '').split('=', 1)
            digest_challenge_pattern[value[0]] = value[1]
        
        return digest_challenge_pattern

    @staticmethod
    def _H(data):
        #return hashlib.md5(data).hexdigest()
        return md5.digest(data) #Optmised for MicroPython

    def _KD(self, secret, data):
        return self._H(secret + ':' + data)

    def _A1(self, realm, nonce, cnonce, algorithm):
        a1 = self.username + ':' + realm + ':' + self.password
        if algorithm[-5:] == '-sess':
            a1 = self._H(self.username + ':' + realm + ':' + self.password) + ':' + nonce + ':' + cnonce

        return a1

    def _A2(self, qop, method, uri, entity_body):
        a2 = method + ':' + uri
        if qop == 'auth-int':
            a2 = method + ':' + uri + ':' + self._H(entity_body)

        return a2

    def authorize(self, method, uri, _challenge, entity_body):
        current, ttl = int(time.time()), 60
        # refresh txinids
        for txnid in [key for key in self.txnids]:
            if self.txnids[txnid]['expire'] < current:
                self.txnids.pop(txnid, None)

        digest_challenge = self._parse_challenge(_challenge)
        nonce = digest_challenge.get('nonce')
        realm = digest_challenge.get('realm')
        qop = digest_challenge.get('qop', '')
        algorithm = digest_challenge.get('algorithm', '')

        if nonce and realm:
            nonce_count = 1
            if nonce in self.txnids:
                nonce_count = self.txnids[nonce]['data']['nc'] + 1

            #cnonce = base64.b64encode(str(current))
            cnonce = ubinascii.b2a_base64(str(current)).decode('utf-8') #Optmised for MicroPython
            nc = '0000000{}'.format(nonce_count)
            if not qop:
                cnonce, nc = '', ''

            A1 = self._A1(realm, nonce, cnonce, algorithm)
            A2 = self._A2(qop, method, uri, entity_body)
            if qop in ['auth', 'auth-int']:
                response = self._KD(self._H(A1), nonce +
                                    ':' + nc +
                                    ':' + cnonce +
                                    ':' + qop +
                                    ':' + self._H(A2))
            else:
                response = self._KD(self._H(A1), nonce + ':' + self._H(A2))
                
            digest_challenge.update({'username': self.username, 'cnonce': cnonce,
                                    'uri': uri, 'nc': nc, 'response': response})

            self.txnids[nonce] = {'expire': current + ttl, 'data': digest_challenge}

            # return credentials
            credentials = 'Digest username="{}"'.format(self.username)
            for key, value in digest_challenge.items():
                if value:
                    credentials += ', {}="{}"'.format(key, value)

            return credentials


# Call status
# =====================================================
def callStatus():
 # Construct API url
 url = host + api_base + "callStatus?format=json"

 #Set the HTTP method
 method = 'GET'
 
 # Headers
 headers = {
    'Content-Type': 'text/plain'
 }

 # Setup a payload
 #payload = json.dumps({"data": "test authentication"})
 payload = '' #EMPTY - no payload required

 #Generate logins/authorisations for `basic` or `digest` auth
 basic_credentials = gen_basic_credential(api_username, api_password)
 auth = DigestAuthorization(api_username, api_password)

 #Make the first request - Identify if `basic` or `digest` auth
 r1st = requests.request(method, url, headers=headers, data=payload)

 #Store details from the request to variables
 _body = r1st.text
 _status = r1st.status_code
 _headers = r1st.headers

 #Debugging
 #logger([_status, _headers, _body])

 # Check the returned status from the request and provide authorisations
 if _status in [401, 407]:
    server_mode = {
        401: {'challenge': 'WWW-Authenticate',
            'credentials': 'authorization'},
        407: {'challenge': 'proxy-authenticate',
            'credentials': 'proxy-authorization'}
    }
    
    #Get the challenge item 'WWW-Authenticate' or 'proxy-authenticate' header
    foundServer_mode = server_mode[_status]['challenge']
    challenge = _headers[foundServer_mode]
    
    #Parse to return if 'Basic' or 'Digest'
    scheme = parse_scheme(challenge)
    
    credentials = 'no-scheme' #Default 'credentials' value

    # If `basic` authorisation
    if scheme == 'Basic':
        credentials = basic_credentials

    # If `digest` authorisation
    if scheme == 'Digest':
        credentials = auth.authorize(method, url, challenge, payload) #from `auth = DigestAuthorization`
    
    # Set the `credentials` headers
    headers[server_mode[_status]['credentials']] = credentials
    
    #Debugging
    #logger(credentials)


    #Make the second request
    r2nd = requests.request(method, url, headers=headers, data=payload)
    
    #Store details from the request to variables
    _body = r2nd
    _status = r2nd.status_code
    _headers = r2nd.headers

    #Debugging
    #logger([r2nd.status_code, r2nd.headers, r2nd.text])

    #logger("Status code:")
    #logger("==============\n")
    #logger(_status)
    
    #logger("Headers:")
    #logger("==============\n")
    #logger(_headers)
    
    #logger("Response body (JSON):")
    #logger("==============\n")
    #logger(_body.json())

    # Use `data` as the variable to return
    data = _body.json()

 # Return the Call Status from `data`
 return data["CallStatus"]["status"]


# Call hangup
def callHangup():
# =====================================================
 # Construct API url
 url = host + api_base + "callSignal?format=json"

 #Set the HTTP method
 method = 'PUT' # Using `PUT` instead of `POST`
 
 # Headers
 headers = {
    'Content-Type': 'application/json'
 }

 # Setup a payload
 payload = json.dumps({"CallSignal":{"cmdType":"hangUp"}}) #JSON data to hang up the call

 #Generate logins/authorisations for `basic` or `digest` auth
 basic_credentials = gen_basic_credential(api_username, api_password)
 auth = DigestAuthorization(api_username, api_password)

 #Make the first request - Identify if `basic` or `digest` auth
 r1st = requests.request(method, url, headers=headers, data=payload)

 #Store details from the request to variables
 _body = r1st.text
 _status = r1st.status_code
 _headers = r1st.headers

 #Debugging
 #logger([_status, _headers, _body])

 # Check the returned status from the request and provide authorisations
 if _status in [401, 407]:
    server_mode = {
        401: {'challenge': 'WWW-Authenticate',
            'credentials': 'authorization'},
        407: {'challenge': 'proxy-authenticate',
            'credentials': 'proxy-authorization'}
    }
    
    #Get the challenge item 'WWW-Authenticate' or 'proxy-authenticate' header
    foundServer_mode = server_mode[_status]['challenge']
    challenge = _headers[foundServer_mode]
    
    #Parse to return if 'Basic' or 'Digest'
    scheme = parse_scheme(challenge)
    
    credentials = 'no-scheme' #Default 'credentials' value

    # If `basic` authorisation
    if scheme == 'Basic':
        credentials = basic_credentials

    # If `digest` authorisation
    if scheme == 'Digest':
        credentials = auth.authorize(method, url, challenge, payload) #from `auth = DigestAuthorization`
    
    # Set the `credentials` headers
    headers[server_mode[_status]['credentials']] = credentials
    
    #Debugging
    #logger(credentials)


    #Make the second request
    r2nd = requests.request(method, url, headers=headers, data=payload)
    
    #Store details from the request to variables
    _body = r2nd
    _status = r2nd.status_code
    _headers = r2nd.headers

    #Debugging
    #logger([r2nd.status_code, r2nd.headers, r2nd.text])

    #logger("Status code:")
    #logger("==============\n")
    #logger(_status)
    
    #logger("Headers:")
    #logger("==============\n")
    #logger(_headers)
    
    #logger("Response body (JSON):")
    #logger("==============\n")
    #logger(_body.json())

    # Use `data` as the variable to return
    data = _body.json()
 
 # Return basedon status
 if data["statusString"] == "OK": 
    return True
 else:
    return False


# Play Sounds - Pass a WAV filename
def playSound(wav_file):
# =====================================================
 audio_out = I2S(
    I2S_id,
    sck=Pin(I2S_sck_pin),   #Serial clock output
    ws=Pin(I2S_ws_pin),     #Word clock output
    sd=Pin(I2S_sd_pin),     #Serial data output
    mode=I2S.TX,
    bits=wav_file_sample_size_in_bits,
    format=wav_file_format,
    rate=sample_rate_in_hz,
    ibuf=I2S_buffer_length_in_bytes,
 )

 #Volume level - DOES THIS WORK?
 #audio_out.volume(70)
 
 wav = open(wav_file, "rb")
 
 # Allocate sample array
 # memoryview used to reduce heap allocation
 wav_samples = bytearray(1000)
 wav_samples_mv = memoryview(wav_samples)
  
 
 # Read audio samples from the WAV file
 # and write them to an I2S DAC
 while True:
    try:
        num_read = wav.readinto(wav_samples_mv)

        # end of WAV file?
        if num_read == 0:
            # end-of-file, advance to first byte of Data section
            # If you want continous looping enable the line below
            #_ = wav.seek(44)
            break
        else:
           _ = audio_out.write(wav_samples_mv[:num_read])
    
    except (KeyboardInterrupt, Exception) as e:
        logger('caught exception {} {}'.format(type(e).__name__, e))
        
        break
 
 # Cleanup
 wav.close()
 audio_out.deinit()

 return True


######################################################
# Logic
######################################################

# Main Code Function
def main():
 try:
    # Loop
    while True:

        # Interval between each request - trying to same some bandwidth and network traffic
        time.sleep(3);
        
        # If connected to WiFi without issues, then continue
        if initWiFi():
        
            # Check call status
            logger("Checking call status")

            # Get the current call status
            current_callstatus = callStatus()

            # If call status is 'ring'
            if current_callstatus == 'ring':
                  logger("Call status is 'ring'")

                  # Pin modifiers from machine
                  from machine import Pin
                  led = machine.Pin('LED', machine.Pin.OUT)   # The LED Pin - This is the internal Pico LED
                  
                  # Turn on the LED
                  led.on()

                  # Play 'ding dong'
                  logger("Playing 'Ding Dong'")
                  playSound(doorbell_sound)

                  # Wait 3 seconds before playing 'ding dong' again
                  logger("Waiting 3 seconds")
                  time.sleep(2);

                  # Play 'ding dong'
                  logger("Playing 'Ding Dong'")
                  playSound(doorbell_sound)

                  # Check if call status is still 'ring' after another 12 seconds
                  logger("Waiting 12 seconds until checking the call status again")
                  time.sleep(12);

                  # Check call status
                  logger("Checking call status")

                  # Get the current call status
                  current_callstatus = callStatus()

                  # If call status is 'ring'
                  if current_callstatus == 'ring':
                        logger("Call status is 'ring'")

                        # Hangup call
                        logger("Hanging up call...")
                        hangup = callHangup()

                        if hangup == True:
                              logger("Call has ended")
                        else:
                              logger("Error ending call")

                  else:
                        logger("Call status is not 'ring'")

                  # Turn off the LED
                  led.off()


            # If call status is 'idle'
            elif current_callstatus == 'idle':
                  logger("Doorbell status is 'idle'")


            # If call status is 'onCall'
            elif current_callstatus == 'onCall':
                  logger("Doorbell status is 'onCall'")


            # Anything else, not covered. There shouldn't be any thing else
            else:
                  logger("Doorbell status is unknown")
        
        
        # Error with WiFi connection
        else:
            logger("Error with WiFi connection")

        # Run Garbage Collection
        gc.collect()


 except KeyboardInterrupt:
    #Debugging
    logger('Keyboard interrupt')

    logger('Cancelling all current calls')
    callHangup()


 except Exception as e:
    #Debugging
    logger('Exception encountered:')
    logger(e)
    #logger('{} | {}'.format(e, traceback.format_exc()))

    logger('Restarting again')

    # Start `main` function
    main()


# Start `main` function
main()
