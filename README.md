# RPI Pico Doorbell Chime

OS/Interpreter: MicroPython
Hardware: Raspberry Pi Pico W

## Description:

Checks ISAPI API status of Hikvision DS-KV6113-WPE1(B) doorbell every few seconds and plays a sound if doorbell is ringing.

Tested on MicroPython v1.19.1, you can download and setup MicroPython on the Pi Pico here: https://www.raspberrypi.com/documentation/microcontrollers/micropython.html

Thonny IDE is used to upload the firmware and to copy over the src files. The files from 'src' must be copied into the root directory on the Pi Pico.

This Python code is run and used to check the ring status of the Hikvision DS-KV6113-WPE1(B) doorbell when used in stand-alone mode. If this ring status is `ring` then the doorbell sound will be played twice. There is then a timeout until the ring status check is performed again.


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
curl -i --digest -u admin:YOUR_PASSWORD http://YOUR_IP/ISAPI/VideoIntercom/callStatus?format=json
```

Shows either `idle`, `ring` or `onCall`

### Hangup a call:
```
curl -i --digest -u admin:YOUR_PASSWORD  -d '{"CallSignal":{"cmdType":"hangUp"}}' -H "Content-Type: application/json" -X PUT http://YOUR_IP/ISAPI/VideoIntercom/callSignal?format=json
```