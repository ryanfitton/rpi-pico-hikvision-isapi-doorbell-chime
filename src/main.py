# coding: utf-8
import base64                              #From `lib/base64.py` lib on local file system
import network                          #Micropython default lib
import urequests as requests            #Micropython default lib
import uping as ping                    #Micropython default lib
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
import utime
import ntptime
import machine                          #Micropython default lib
from machine import I2S                 #Micropython default lib
from machine import I2S                 #Micropython default lib
from machine import WDT                 #Micropython default lib
#from machine import RTC                #Micropython default lib
from machine import Pin                 #Micropython default lib
from machine import WDT                 #Micropython default lib
import gc                               #Micropython default lib
import _thread                          #Micropython default lib



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
host=""                                             #The Doorbell - Highly recommended to setup static DHCP mappings for this device on your router
protocol="http://"                                  #Protocol to be used, usually 'http://'
api_base_intercom="/ISAPI/VideoIntercom/"           #Intercom URL Base for Doorbell API
api_base_streaming="/ISAPI/Streaming/"              #Streaming URL Base for Doorbell API

#Pushover Message API Configuration
use_pushover=False                                  #Enable/Disable Pushover functionality
pushover_token=""                                   #The Pushover APP token - Register on https://pushover.net/ to generate a token
pushover_user=""                                    #The Pushover APP user or group key - Configure this on https://pushover.net/
pushover_host="api.pushover.net"                    #The hostname
pushover_protocol="https://"                        #Protocol to be used, usually 'https://'
pushover_api_base_message="/1/messages.json"        #URL Base for messages API
pushover_message="Someone is at your door!"         #Message for the doorbell message

#WAV Audio File Configuration
#8000Hz, 16-Bit PCM
wifi_connected_sound="wifi-connected.wav"           #Function to play sound is currently commented out below

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

# Pin modifiers from machine
led = machine.Pin('LED', machine.Pin.OUT)   # The LED Pin - This is the internal Pico LED



# Start Watchdog
# =====================================================
wdt = WDT(timeout=8388)  # enable it with a timeout of 2s



######################################################
# Functions
######################################################

# Watchdog Feed
# =====================================================
def feedWatchdog():
 # Feed the watchdog to prevent system from halting
 wdt.feed()


# Initialise WiFi
# =====================================================
def initWiFi():
 feedWatchdog() # Feed Watchdog

 wlan = network.WLAN(network.STA_IF)    # Create an object
 wlan.active(True)                    # Turn on the Raspberry Pi Pico W’s Wi-Fi
 wlan.connect(ssid, ssid_password)    # Connect to your router using the SSID and PASSWORD
 
 # Wait for connection or failure
 max_wait = 10
 while max_wait > 0:
    feedWatchdog() # Feed Watchdog
 
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1

    #Debugging
    logger('Connecting to WiFi...')

    feedWatchdog() # Feed Watchdog

    time.sleep(1)

    feedWatchdog() # Feed Watchdog
 
 # Handle connection errors
 if wlan.status() != 3:
    feedWatchdog() # Feed Watchdog

    raise Exception('Network connection failed')

    return False

 # If connected
 else:
    feedWatchdog() # Feed Watchdog

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


# WiFi Connected Notification
# =====================================================
def wifiConnectedNotify():
 feedWatchdog() # Feed Watchdog

 logger("WiFi is connected")
 
 # Play sound
 #playSound(wifi_connected_sound)

 # Flash the LED
 for i in range(20):
    feedWatchdog() # Feed Watchdog
    
    led.on()
    time.sleep(0.1)
    
    led.off()
    time.sleep(0.1)


# Message logger - Mainly for debugging
# =====================================================
def logger(message):
    feedWatchdog() # Feed Watchdog

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
 feedWatchdog() # Feed Watchdog

 # Construct API url
 url = protocol + host + api_base_intercom + "callStatus?format=json"

 #Set the HTTP method
 method = 'GET'
 
 # Headers
 headers = {
    'Content-Type': 'text/plain'
 }

 # Setup a payload
 #payload = json.dumps({"data": "test authentication"})
 payload = '' #EMPTY - no payload required

 feedWatchdog() # Feed Watchdog

 #Generate logins/authorisations for `basic` or `digest` auth
 basic_credentials = gen_basic_credential(api_username, api_password)
 auth = DigestAuthorization(api_username, api_password)

 feedWatchdog() # Feed Watchdog

 #Make the first request - Identify if `basic` or `digest` auth
 r1st = requests.request(method, url, headers=headers, data=payload)

 feedWatchdog() # Feed Watchdog

 #Store details from the request to variables
 _body = r1st.text
 _status = r1st.status_code
 _headers = r1st.headers

 #Debugging
 #logger([_status, _headers, _body])

 feedWatchdog() # Feed Watchdog
 
 # Check the returned status from the request and provide authorisations
 if _status in [401, 407]:
    server_mode = {
        401: {'challenge': 'WWW-Authenticate',
            'credentials': 'authorization'},
        407: {'challenge': 'proxy-authenticate',
            'credentials': 'proxy-authorization'}
    }
    
    feedWatchdog() # Feed Watchdog
    
    #Get the challenge item 'WWW-Authenticate' or 'proxy-authenticate' header
    foundServer_mode = server_mode[_status]['challenge']
    challenge = _headers[foundServer_mode]

    feedWatchdog() # Feed Watchdog
    
    #Parse to return if 'Basic' or 'Digest'
    scheme = parse_scheme(challenge)
    
    credentials = 'no-scheme' #Default 'credentials' value

    # If `basic` authorisation
    if scheme == 'Basic':
        credentials = basic_credentials

    # If `digest` authorisation
    if scheme == 'Digest':
        credentials = auth.authorize(method, url, challenge, payload) #from `auth = DigestAuthorization`

    feedWatchdog() # Feed Watchdog
    
    # Set the `credentials` headers
    headers[server_mode[_status]['credentials']] = credentials
    
    #Debugging
    #logger(credentials)

    feedWatchdog() # Feed Watchdog

    #Make the second request
    r2nd = requests.request(method, url, headers=headers, data=payload)
    
    #Store details from the request to variables
    _body = r2nd
    _status = r2nd.status_code
    _headers = r2nd.headers

    feedWatchdog() # Feed Watchdog

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

    feedWatchdog() # Feed Watchdog

 # Return the Call Status from `data`
 return data["CallStatus"]["status"]


# Call hangup
# =====================================================
def callHangup():
 feedWatchdog() # Feed Watchdog

 # Construct API url
 url = protocol + host + api_base_intercom + "callSignal?format=json"

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

    feedWatchdog() # Feed Watchdog


# Get image capture
# =====================================================
def imageCapture():
 feedWatchdog() # Feed Watchdog

 # Construct API url
 url = protocol + host + api_base_streaming + "channels/101/picture"

 #Set the HTTP method
 method = 'GET'
 
 # Headers
 headers = {
    'Content-Type': 'text/plain'
 }

 # Setup a payload
 #payload = json.dumps({"data": "test authentication"})
 payload = '' #EMPTY - no payload required

 feedWatchdog() # Feed Watchdog

 #Generate logins/authorisations for `basic` or `digest` auth
 basic_credentials = gen_basic_credential(api_username, api_password)
 auth = DigestAuthorization(api_username, api_password)

 feedWatchdog() # Feed Watchdog

 #Make the first request - Identify if `basic` or `digest` auth
 r1st = requests.request(method, url, headers=headers, data=payload)

 feedWatchdog() # Feed Watchdog

 #Store details from the request to variables
 _body = r1st.text
 _status = r1st.status_code
 _headers = r1st.headers

 #Debugging
 #logger([_status, _headers, _body])

 feedWatchdog() # Feed Watchdog
 
 # Check the returned status from the request and provide authorisations
 if _status in [401, 407]:
    server_mode = {
        401: {'challenge': 'WWW-Authenticate',
            'credentials': 'authorization'},
        407: {'challenge': 'proxy-authenticate',
            'credentials': 'proxy-authorization'}
    }
    
    feedWatchdog() # Feed Watchdog
    
    #Get the challenge item 'WWW-Authenticate' or 'proxy-authenticate' header
    foundServer_mode = server_mode[_status]['challenge']
    challenge = _headers[foundServer_mode]

    feedWatchdog() # Feed Watchdog
    
    #Parse to return if 'Basic' or 'Digest'
    scheme = parse_scheme(challenge)
    
    credentials = 'no-scheme' #Default 'credentials' value

    # If `basic` authorisation
    if scheme == 'Basic':
        credentials = basic_credentials

    # If `digest` authorisation
    if scheme == 'Digest':
        credentials = auth.authorize(method, url, challenge, payload) #from `auth = DigestAuthorization`

    feedWatchdog() # Feed Watchdog
    
    # Set the `credentials` headers
    headers[server_mode[_status]['credentials']] = credentials
    
    #Debugging
    #logger(credentials)

    feedWatchdog() # Feed Watchdog

    #Make the second request
    r2nd = requests.request(method, url, headers=headers, data=payload)
    
    #Store details from the request to variables
    _body = r2nd
    _status = r2nd.status_code
    _headers = r2nd.headers

    feedWatchdog() # Feed Watchdog

    #Debugging
    #logger([r2nd.status_code, r2nd.headers, r2nd.text])

    #logger("Status code:")
    #logger("==============\n")
    #logger(_status)
    
    #logger("Headers:")
    #logger("==============\n")
    #logger(_headers)
    
    #logger("Response body (Content):")
    #logger("==============\n")
    #logger(_body.content)


    # Use `data` as the variable to return
    # Return the base64 encoded image
    data = base64.b64encode(_body.content).decode('utf-8')

    feedWatchdog() # Feed Watchdog

 # Return the image embedded in the `data` variable
 return data


# Send Pushover message
# =====================================================
def sendPushoverMessage(message, attachment_base64=False, attachment_type='image/jpeg'):
 feedWatchdog()  # Feed Watchdog

 # Construct API url
 url = pushover_protocol + pushover_host + pushover_api_base_message

 # Decode base64 to bytes
 if attachment_base64:
    image_bytes = ubinascii.a2b_base64(attachment_base64)
 else:
    image_bytes = b''

 # Prepare multipart/form-data
 boundary = '----WebKitFormBoundary{}'.format(machine.unique_id().hex())
 headers = {
    'Content-Type': f'multipart/form-data; boundary={boundary}'
 }

 # Build multipart body
 body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="token"\r\n\r\n{pushover_token}\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="user"\r\n\r\n{pushover_user}\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="message"\r\n\r\n{message}\r\n'
 ).encode('utf-8')

 if image_bytes:
    body += (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="attachment"; filename="image.jpg"\r\n'
        f'Content-Type: {attachment_type}\r\n\r\n'
    ).encode('utf-8') + image_bytes + f'\r\n'.encode('utf-8')

 body += f'--{boundary}--\r\n'.encode('utf-8')

 # Send the request
 import urequests as requests
 response = requests.post(url, headers=headers, data=body)
 _status = response.status_code

 if _status == 200:
    data = "Pushover sent."
 else:
    data = f"Pushover error: {response.text}"

 return data

 
 # Is this still required?
 # Return basedon status
 #if data["statusString"] == "OK": 
 #   return True
 #else:
 #   return False


# Play Sounds - Pass a WAV filename
# =====================================================
def playSound(wav_file):
 feedWatchdog() # Feed Watchdog

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
    feedWatchdog() # Feed Watchdog

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
        feedWatchdog() # Feed Watchdog

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
 feedWatchdog() # Feed Watchdog

 # Turn on the LED
 led.on()
 
 # Run Wifi Connection at startup
 # =====================================================

 # If connected to WiFi without issues, then continue
 if initWiFi():
    feedWatchdog() # Feed Watchdog

    # WiFi is connected - Send a notification to the user
    wifiConnectedNotify()


    # Check doorbell is available on the network
    # pingDevice = ping.ping(host, count=4, timeout=2500, interval=10, quiet=True, size=64)
            
    # If any value from Ping is zero, usually the second will show this.
    # First: n_trans - ping attempts
    # Second: n_recv - packets recieved
    # for pingValue in pingDevice:
    #    if pingValue == 0:
    #        logger('Ping (ICMP) packets have not been recieved. It appears the device is offline.')
    #    
    #    else:
    #        logger('Ping (ICMP) packets have been recieved. It appears the device is online.')
    
    

    # Start logic function
    # =====================================================
    logger("Starting logic function")
    
    def logic():
     feedWatchdog() # Feed Watchdog

     # Turn off the LED
     led.off()

     logger("Running")
    
     # Try code and capture any Keyboard Interrupts or Exceptions
     try:
        feedWatchdog() # Feed Watchdog
        
        # Variables
        # =====================================================
        initialTicks = utime.ticks_ms()
     
        WiFiInterval = 600000 #Check the Wifi every: Milliseconds - 600000 = 10 minutes
        WiFiNowTicks = initialTicks
        WiFiNowTicksDeadline = 0
     
        CallStatusInterval = 2000 #Check the Doorbell Call Status every: Milliseconds - 2000 = 2 seconds
        CallStatusNowTicks = initialTicks
        CallStatusNowDeadline = 0

        GarbageCollectionInterval = 600000 #Run the Garbage Collection every: Milliseconds - 600000 = 10 minutes
        GarbageCollectionNowTicks = initialTicks
        GarbageCollectionDeadline = 0

        i = 0 # Loop counter
        
        # Loop
        while True:    
            feedWatchdog() # Feed Watchdog

            time.sleep(1)

            feedWatchdog() # Feed Watchdog

            # Debugging
            #logger("Loop:")
            #logger(i)


            # Garbage Collection
            # =====================================================
            
            # Set a deadline for of 20 seconds since inital script start
            GarbageCollectionDeadline = utime.ticks_add(GarbageCollectionNowTicks, GarbageCollectionInterval)

            # Current time is greater than deadline
            if utime.ticks_ms() >= GarbageCollectionDeadline:
                feedWatchdog() # Feed Watchdog
                
                #logger("GarbageCollectionDeadline dealine has been reached")
                
                # Run Garbage Collection
                logger("Running Garbage Collection")
                gc.collect()
                logger("Finished Garbage Collection")

                # Update the ticks with current ticks
                GarbageCollectionNowTicks = utime.ticks_ms()
            

            
            # WiFi Connection check
            # =====================================================
            
            # Set a deadline for of 10 seconds since inital script start
            WiFiDeadline = utime.ticks_add(WiFiNowTicks, WiFiInterval)
            
            # Current time is greater than deadline
            if utime.ticks_ms() >= WiFiDeadline:
                feedWatchdog() # Feed Watchdog

                #logger("WiFiDeadline has been reached")
                
                # Check WiFi connection
                if initWiFi():
                    feedWatchdog() # Feed Watchdog

                    # WiFi is connected
                    ("WiFi is connected")
                else:
                    feedWatchdog() # Feed Watchdog

                    # Error with WiFi connection
                    logger("Error with WiFi connection")

                    # Exception raised
                    logger("Error with WiFi connection")
                    raise Exception('Network connection failed')

                feedWatchdog() # Feed Watchdog
                
                # Sleep for a few seconds to ensure network is fully ready
                time.sleep(2)

                feedWatchdog() # Feed Watchdog
                
                # Update the ticks with current ticks
                WiFiNowTicks = utime.ticks_ms()



            # Door bell call status check
            # =====================================================
            
            # Set a deadline for of 5 seconds since inital script start
            CallStatusDeadline = utime.ticks_add(CallStatusNowTicks, CallStatusInterval)
            
            # Current time is greater than deadline
            if utime.ticks_ms() >= CallStatusDeadline:
                feedWatchdog() # Feed Watchdog

                #logger("CallStatusDeadline dealine has been reached")
      
                # If call status is 'ring' (Ringing - Someone has pushed the doorbell)
                if callStatus() == 'ring':

                    # Turn on the LED
                    led.on()

                    # Core 0 task - default
                    def core0_task():
                        logger("Running on Core 0 ****")

                        feedWatchdog() # Feed Watchdog
                        
                        logger("Call status is 'ring'")

                        # Play 'ding dong'
                        logger("Playing 'Ding Dong'")
                        playSound(doorbell_sound)
                        
                        logger("'Ding Dong' again in 3 seconds")
                        
                        feedWatchdog() # Feed Watchdog

                        time.sleep(3)

                        feedWatchdog() # Feed Watchdog
                        
                        # Play 'ding dong'
                        logger("Playing 'Ding Dong'")
                        playSound(doorbell_sound)

                        feedWatchdog() # Feed Watchdog

                        # Check if call status is still 'ring' after another 5 seconds
                        logger("Waiting 5 seconds until checking the call status again")

                        feedWatchdog() # Feed Watchdog
                        
                        time.sleep(5)
                        
                        # Check if call status is still 'ring' after another 5 seconds
                        logger("Waiting another 5 seconds until checking the call status again")

                        feedWatchdog() # Feed Watchdog
                        
                        time.sleep(5)
                        
                        # If call status is 'ring'
                        if callStatus() == 'ring':
                            feedWatchdog() # Feed Watchdog
                            
                            logger("Call status is 'ring'")

                            # Hangup call after 3 seconds
                            logger("Hanging up call...")
                            time.sleep(3)
                            hangup = callHangup()

                            feedWatchdog() # Feed Watchdog

                            if hangup == True:
                                logger("Call has ended")
                            else:
                                logger("Error ending call")

                        # If call status is no longer 'ring'
                        else:
                            feedWatchdog() # Feed Watchdog
                            
                            logger("Call status is no longer 'ring'")


                    # Core 1 task - Runs on a new core
                    def core1_task():
                        logger("Running on Core 1 ****")

                        feedWatchdog() # Feed Watchdog

                        logger("Getting an image capture...")
                        ImageCapture = imageCapture()           # Get an image capture in base64 encoded format

                        feedWatchdog() # Feed Watchdog

                        #logger("Image capture (Base64):")
                        #logger(ImageCapture)

                        feedWatchdog() # Feed Watchdog
                        
                        if use_pushover is not False:
                            logger("Sending Pushover message...")
                            sendPushoverMessage(pushover_message, ImageCapture)    # Send a Pushover message

                        time.sleep(10)


                    # Start a new thread on Core 1 and run tasks
                    _thread.start_new_thread(core1_task, ())

                    # Core 0 - Run usual tasks
                    core0_task()

                    # Turn off the LED
                    led.off()

                
                # Update the ticks with current ticks
                CallStatusNowTicks = utime.ticks_ms()

                feedWatchdog() # Feed Watchdog
            
            
            
            # Increase counter by 1
            i += 1



     except KeyboardInterrupt:
        feedWatchdog() # Feed Watchdog

        # Debugging
        logger('Keyboard interrupt')

        # Cancel all calls after 3 seconds
        logger('Cancelling all current calls')
        time.sleep(3)
        callHangup()

        feedWatchdog() # Feed Watchdog


     except Exception as e:
        feedWatchdog() # Feed Watchdog
        
        # Debugging
        logger('Exception encountered:')
        logger(e)
        #logger('{} | {}'.format(e, traceback.format_exc()))

        logger('Restarting again')

        feedWatchdog() # Feed Watchdog

        # Retart `logic` function
        logic()

     
    feedWatchdog() # Feed Watchdog
    
    # Start `logic` function
    logic()



 # Error with WiFi connection
 else:
    logger("Error with WiFi connection")

    feedWatchdog() # Feed Watchdog

    # Restart `main` function
    main()


feedWatchdog() # Feed Watchdog

# Start `main` function
main()
