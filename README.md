# home-assistant-homematic
Integrating homematic devices into Home-Assistant using pyhomematic

**WARNING: Currently experimental.**

###Currently only following HA device types are supported:
- Light
- Switch
- Rollershutter
- Binary_sensor (partially)

###Installation:
1. Make sure pyhomematic (https://github.com/danielperna84/pyhomematic) is installed. 
2. Copy files into homeassistant\components and subfolders. **Do not place them in .homeassistant/custom_components/**

Devices are depended on mapping in pyhomematic (only few Homematic devices exist there. Appending in _devices.py (bottom) could be a good idea. ([Click here for more info](https://github.com/jazzaj/home-assistant-homematic/issues/1#issuecomment-217735948))

###Configuration as for other HA platformms (configuration.yaml).

Example extract from configuration.yaml:
```
homematic:
  local_ip: "192.X.X.X"          # IP of machine running home-assistant
  local_port: 8059               # Port of machine running home-assistant (can be freely defined)
  remote_ip: "192.X.X.X"         # IP of CCU/CCU2/Homegear (can also be 127.0.0.1 if Homegear runs on the same machine)
  remote_port: 2001              # Port of CCU/CCU2/Homegear XML RPC Server (default: 2001)
  autodetect: 'False'            # If true all known devices are added automatically. No configuration of devices in configuration.yaml required (currently experimental!)
 
switch:
    platform: homematic
    address: 'JEQxxxxxxx'
    name: 'TV set'

light:
    platform: homematic
    address: 'LEQxxxxxxx'
    name: 'Sideboard Light'

rollershutter:
    platform: homematic
    address: 'KEQxxxxxxx'
    name: 'Kitchen'

binary_sensor:
    platform: homematic
    address: 'KEQxxxxxxx'
    name: 'Door'
```
