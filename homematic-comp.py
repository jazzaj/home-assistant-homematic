"""
Support for Homematic Devices.
"""
import logging

from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP
from homeassistant.loader import get_component
from homeassistant.helpers import validate_config
from homeassistant.helpers.entity import ToggleEntity

REQUIREMENTS = ['pyhomematic']
DOMAIN = 'homematic'

HOMEMATIC = None

LOCAL_IP = "LOCAL_IP"
LOCAL_PORT = "LOCAL_PORT"
REMOTE_IP = "REMOTE_IP"
REMOTE_PORT = "REMOTE_PORT"

DISCOVER_SWITCHES = "homematic.switches"
DISCOVER_SENSORS = "homematic.sensors"
DISCOVER_BINARY_SENSORS = "homematic.binary_sensors"
DISCOVER_ROLLERSHUTTER = "homematic.rollershutter"


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
        logger.error("Missing required configuration item %s or %s",
                     LOCAL_IP, LOCAL_PORT, REMOTE_IP, REMOTE_PORT)
        return

    import homematic
    
    homematic.create_server(local=local_ip, localport=local_port, remote=remote_ip, remoteport=remote_port, systemcallback=homematic_callback) # Create server thread
    homematic.start() # Start server thread, connect to homegear, initialize to receive events
    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, homematic.stop) # Stops server when Homeassistant is shuting down
    # TODO: Query server for all devices?
    HOMEMATIC = homematic

    for component_name, func_exists, discovery_type in (
        ('switch', get_switches, DISCOVER_SWITCHES),
        ('rollershutter', get_rollershutters, DISCOVER_ROLLERSHUTTER),
        ('binary_sensor', get_remote_channels, DISCOVER_BINARY_SENSORS),
        ('sensor', get_thermostats, DISCOVER_SENSORS)
        ):

        if func_exists():
            component = get_component(component_name) 

            # Ensure component is loaded
            bootstrap.setup_component(hass, component.DOMAIN, config)

            # Fire discovery event
            hass.bus.fire(EVENT_PLATFORM_DISCOVERED, {
                ATTR_SERVICE: discovery_type,
                ATTR_DISCOVERED: {}
            })
    return True


def get_switches():
    from homematic import _devices
    return get_devices([HMSwitch])


def get_rollershutters():
    from homematic import _devices
    return get_devices([HMRollerShutter])


def get_remote_channels():
    from homematic import _devices
    return get_devices([HMRemoteChannels])


def get_thermostats():
    from homematic import _devices
    return get_devices([HMThermostat])


def get_devices(device_types):
    global HOMEMATIC
    
    matched_devices = []
    for key in HOMEMATIC.devices_all:
        for device_type in device_types:            
            if isinstance(HOMEMATIC.devices_all[key], device_type):
                matched_devices.append(HOMEMATIC.devices_all[key])
    return matched_devices


def syscb(src, *args):
    print(src)
    for arg in args:
        print(arg)
def cb1(address, interface_id, key, value):
    print("CALLBACK WITH CHANNELS: %s, %s, %s, %s" % (address, interface_id, key, value))
def cb2(address, interface_id, key, value):
    print("CALLBACK WITHOUT CHANNELS: %s, %s, %s, %s" % (address, interface_id, key, value))

import homematic
homematic.create_server(local="192.168.178.71", localport=8061, remote="192.168.178.241", remoteport=2001, systemcallback=syscb) # Create server thread
# homematic.create_server(local="192.168.178.241", localport=2001, remote="192.168.178.71", remoteport=8061, systemcallback=syscb) # Create server thread
print("Server created.")
homematic.start() # Start server thread, connect to homegear, initialize to receive events
print("Server started.")
homematic.devices['address_of_rollershutter_device'].move_down() # Move rollershutter down
homematic.devices_all['address_of_doorcontact:1'].getValue("STATE") # True or False, depending on state
homematic.devices['address_of_doorcontact'].setEventCallback(cb1) # Add first callback
homematic.devices['address_of_doorcontact'].setEventCallback(cb2, bequeath=False) # Add second callback
homematic.stop() # Shutdown to finish the server thread and quit