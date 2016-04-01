"""
Support for Homematic Devices.
Using pyhomematic to start a XML-RPC Server for communication with Homematic devices.
Require before configuration of any Homematic device
Autodetection ability can be turned on or off.

Configuration example:

homematic:
  loacal_ip: "<IP of device running Home Assistant>"
  local_port: <Port for connection with Home Assistant>
  remote_ip: "<IP of Homegear / CCU>"
  remote_port: <Port of Homegear / CCU XML-RPC Server>
  autodetect: <'True' or  'False'> # Defines if all devices detected are automatically added to Home Assistant. Not yet fully working
  
"""

import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STOP, EVENT_PLATFORM_DISCOVERED, ATTR_SERVICE, ATTR_DISCOVERED 
from homeassistant.loader import get_component
import homeassistant.bootstrap
from homeassistant.helpers import validate_config
from homeassistant.helpers.entity import ToggleEntity
from collections import OrderedDict
import time
    

# REQUIREMENTS = ['pyhomematic']
DOMAIN = 'homematic'

HOMEMATIC = None

LOCAL_IP = "local_ip"
LOCAL_PORT = "local_port"
REMOTE_IP = "remote_ip"
REMOTE_PORT = "remote_port"
AUTODETECT = "autodetect"

DISCOVER_SWITCHES = "homematic.switch"
DISCOVER_LIGHTS = "homematic.light"
DISCOVER_SENSORS = "homematic.sensor"
DISCOVER_BINARY_SENSORS = "homematic.binary_sensor"
DISCOVER_ROLLERSHUTTER = "homematic.rollershutter"

ATTR_DISCOVER_DEVICES = "devices"
ATTR_DISCOVER_CONFIG = "config"

HM_DEVICE_TYPES = {
   DISCOVER_SWITCHES : ['HMSwitch'],
   DISCOVER_LIGHTS: ['HMDimmer'],
   DISCOVER_SENSORS : ['HMCcu', 'HMThermostat'],
   DISCOVER_BINARY_SENSORS : ['HMRemote', 'HMDoorContact'],
   DISCOVER_ROLLERSHUTTER : ['HMRollerShutter']
}


# pylint: disable=unused-argument
def setup(hass, config):
    """Setup the Homematic component."""
    
    global HOMEMATIC

    logger = logging.getLogger(__name__)
    local_ip = config[DOMAIN].get(LOCAL_IP)
    local_port = config[DOMAIN].get(LOCAL_PORT)
    remote_ip = config[DOMAIN].get(REMOTE_IP)
    remote_port = config[DOMAIN].get(REMOTE_PORT)
    autodetect = str(config[DOMAIN].get(AUTODETECT, False)).upper() == 'TRUE'
    
    if local_ip is None or local_port is None or remote_ip is None or remote_port is None: 
        logger.error("Missing required configuration item %s, %s, %s or %s",
                     LOCAL_IP, LOCAL_PORT, REMOTE_IP, REMOTE_PORT)
        return

    import pyhomematic
    #import homematic as pyhomematic
    
    HOMEMATIC = pyhomematic
    HOMEMATIC.create_server(local=local_ip, localport=local_port, remote=remote_ip, remoteport=remote_port) # Create server thread
    HOMEMATIC.start() # Start server thread, connect to homegear, initialize to receive events
    # TODO: Replace waiting with something more general...
    time.sleep(4) 
    print('Homematic Devices found: ', len(HOMEMATIC.devices))
    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, HOMEMATIC.stop) # Stops server when Homeassistant is shuting down
    hass.config.components.append(DOMAIN)
    
    if not autodetect:
        return True

    for component_name, func_get_devices, discovery_type in (
        ('switch', get_switches, DISCOVER_SWITCHES),
        ('light', get_lights, DISCOVER_LIGHTS),
        ('rollershutter', get_rollershutters, DISCOVER_ROLLERSHUTTER),
        ('binary_sensor', get_binary_sensors, DISCOVER_BINARY_SENSORS),
        ('sensor', get_sensors, DISCOVER_SENSORS)
        ):

        found_devices = func_get_devices()
        # found_devices = None
        
        if found_devices:
            component = get_component(component_name)
            config ={component.DOMAIN : found_devices}

            # Ensure component is loaded
            homeassistant.bootstrap.setup_component(hass, component.DOMAIN, config)

            # Fire discovery event
            hass.bus.fire(EVENT_PLATFORM_DISCOVERED, {
                ATTR_SERVICE: discovery_type,
                ATTR_DISCOVERED: {ATTR_DISCOVER_DEVICES: found_devices, 
                ATTR_DISCOVER_CONFIG: ''}
            })
    return True


def get_switches():
    return get_devices(HM_DEVICE_TYPES[DISCOVER_SWITCHES])


def get_lights():
    return get_devices(HM_DEVICE_TYPES[DISCOVER_LIGHTS])


def get_rollershutters():
    return get_devices(HM_DEVICE_TYPES[DISCOVER_ROLLERSHUTTER])


def get_binary_sensors():
    return get_devices(HM_DEVICE_TYPES[DISCOVER_BINARY_SENSORS])


def get_sensors():
    return get_devices(HM_DEVICE_TYPES[DISCOVER_SENSORS])


def get_devices(device_types):
    global HOMEMATIC
    
    device_arr = []
    for key in HOMEMATIC.devices:
        if HOMEMATIC.devices[key].__class__.__name__ in device_types:
            ordered_device_dict = OrderedDict()
            ordered_device_dict['platform'] = 'homematic'
            ordered_device_dict['key'] = key
            ordered_device_dict['name'] = key
            device_arr.append(ordered_device_dict)
    return device_arr
