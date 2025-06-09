# RPI Pico Doorbell Chime

OS/Interpreter: MicroPython
Hardware: Raspberry Pi Pico W or Raspberry Pi Pico 2 W

## Description:

Checks ISAPI API status of Hikvision DS-KV6113-WPE1(B) doorbell every few seconds and plays a sound if doorbell is ringing.

Tested on MicroPython v1.19.1, you can download and setup MicroPython on the Pi Pico here: https://www.raspberrypi.com/documentation/microcontrollers/micropython.html

Thonny IDE is used to upload the firmware and to copy over the src files. The files from 'src' must be copied into the root directory on the Pi Pico.

Download up to date firmware here:
* Pico W (1st Gen): https://micropython.org/download/RPI_PICO_W/
* Pico W (2nd Gen): https://micropython.org/download/RPI_PICO2_W/

This Python code is run and used to check the ring status of the Hikvision DS-KV6113-WPE1(B) doorbell when used in stand-alone mode. If this ring status is `ring` then the doorbell sound will be played twice. There is then a timeout until the ring status check is performed again.

View my blog post for this project: https://ryanfitton.co.uk/blog/diy-doorbell-chime-for-hikvision-isapi-with-a-raspberry-pi-pico/


## Getting started:

To get started edit the config in `src/main.py` for the following fields:

### WiFi Configuration:
* `ssid` : WiFi network name
* `ssid_password` : WiFi network password

### Doorbell API Configuration:
* `api_username` : Doorbell Admin user
* `api_password` : Doorbell Admin user's password
* `host` : The Doorbell's IP Address- Highly recommended to setup static DHCP mappings for this device on your router

### Pushover Message API Configuration:
* `use_pushover` : Enable/Disable Pushover functionality, set `true` or `false`. If true then also configure the below:
* `pushover_token` : The Pushover APP token - Register on https://pushover.net/ to generate a token
* `pushover_user` : The Pushover APP user or group key - Configure this on https://pushover.net/
* `pushover_message` : Message for the doorbell message


## Parts:

* RPI Pico Wireless with Headers
* Room Sensor Enclosure - Size 2 (with Pi HAT / 3A+ Mounts) - Vented (https://thepihut.com/products/room-sensor-enclosure-size-2-with-pi-3a-mounts?variant=39957973008579)
* Premium Female/Female Jumper Wires - 20 x 3" (75mm) (https://thepihut.com/products/premium-female-female-jumper-wires-20-x-3-75mm?variant=27739698577)
* Adafruit I2S 3W Class D Amplifier Breakout - MAX98357A (https://thepihut.com/products/adafruit-i2s-3w-class-d-amplifier-breakout-max98357a?variant=27740275281)
* Stereo Enclosed Speaker Set - 3W 4 Ohm (https://thepihut.com/products/stereo-enclosed-speaker-set-3w-4-ohm?variant=27739539793)



## Testing:

You can run these curl commands on your computer to test the Hikvision DS-KV6113-WPE1(B) doorbell.

* Replace `YOUR_PASSWORD` with your doorbell admin user's password
* Replace `YOUR_IP` with your doorbell IP address

### Get status:

```
curl -i --digest -u admin:YOUR_PASSWORD "http://YOUR_IP/ISAPI/VideoIntercom/callStatus?format=json"
```

Shows either `idle`, `ring` or `onCall`

### Hangup a call:
```
curl -i --digest -u admin:YOUR_PASSWORD  -d '{"CallSignal":{"cmdType":"hangUp"}}' -H "Content-Type: application/json" -X PUT "http://YOUR_IP/ISAPI/VideoIntercom/callSignal?format=json"
```

### Get an image capture:
```
curl -i --digest -u admin:YOUR_PASSWORD "http://YOUR_IP/ISAPI/Streaming/channels/101/picture"
```