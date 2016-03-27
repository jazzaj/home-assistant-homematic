"""
Support for Homematic Devices.
"""
import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STOP, EVENT_PLATFORM_DISCOVERED, ATTR_SERVICE, ATTR_DISCOVERED 
from homeassistant.loader import get_component
import homeassistant.bootstrap
from homeassistant.helpers import validate_config
from homeassistant.helpers.entity import ToggleEntity
import time
    

# REQUIREMENTS = ['pyhomematic']
DOMAIN = 'homematic'

HOMEMATIC = None

LOCAL_IP = "LOCAL_IP"
LOCAL_PORT = "LOCAL_PORT"
REMOTE_IP = "REMOTE_IP"
REMOTE_PORT = "REMOTE_PORT"

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
    
    def homematic_callback(source, *args):
        """ """
        # TODO: Add callbacks
        pass
           
    global HOMEMATIC

    logger = logging.getLogger(__name__)
    local_ip = config[DOMAIN].get(LOCAL_IP)
    local_port = config[DOMAIN].get(LOCAL_PORT)
    remote_ip = config[DOMAIN].get(REMOTE_IP)
    remote_port = config[DOMAIN].get(REMOTE_PORT)
    
    if local_ip is None or local_port is None or remote_ip is None or remote_port is None: 
        logger.error("Missing required configuration item %s, %s, %s or %s",
                     LOCAL_IP, LOCAL_PORT, REMOTE_IP, REMOTE_PORT)
        return

    import pyhomematic

    HOMEMATIC = pyhomematic
    HOMEMATIC.create_server(local=local_ip, localport=local_port, remote=remote_ip, remoteport=remote_port, systemcallback=homematic_callback) # Create server thread
    HOMEMATIC.start() # Start server thread, connect to homegear, initialize to receive events
    time.sleep(4) # TODO: Replace waiting with something more general...
    print('Homematic Devices found: ', len(HOMEMATIC.devices))
    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, HOMEMATIC.stop) # Stops server when Homeassistant is shuting down

    for component_name, func_get_devices, discovery_type in (
        ('switch', get_switches, DISCOVER_SWITCHES),
        ('light', get_lights, DISCOVER_LIGHTS),
        ('rollershutter', get_rollershutters, DISCOVER_ROLLERSHUTTER),
        ('binary_sensor', get_binary_sensors, DISCOVER_BINARY_SENSORS),
        ('sensor', get_sensors, DISCOVER_SENSORS)
        ):

        # TODO Check and modify: TypeError: 'HMSwitch' object is not iterable
        # found_devices = func_get_devices()
        found_devices = None
        
        if found_devices:
            component = get_component(component_name) 

            # Ensure component is loaded
            homeassistant.bootstrap.setup_component(hass, component.DOMAIN, config)

            # signal_repetitions = config[DOMAIN].get(ATTR_SIGNAL_REPETITIONS, DEFAULT_SIGNAL_REPETITIONS)
            # Fire discovery event
            hass.bus.fire(EVENT_PLATFORM_DISCOVERED, {
                ATTR_SERVICE: discovery_type,
                ATTR_DISCOVERED: {ATTR_DISCOVER_DEVICES: found_devices, 
                ATTR_DISCOVER_CONFIG: ''}
                                # switch.id for switch in devices
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
    
    matched_devices = []
    for key in HOMEMATIC.devices:
        if HOMEMATIC.devices[key].__class__.__name__ in device_types:
            matched_devices.append(HOMEMATIC.devices[key])
    return matched_devices
