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
# from homeassistant.helpers import validate_config
# from homeassistant.helpers.entity import ToggleEntity
from collections import OrderedDict
# import time
    
# REQUIREMENTS = ['pyhomematic']
# DEPENDENCIES = ['pyhomematic']

import pyhomematic
homematic_devices = {}
HOMEMATIC = pyhomematic

DOMAIN = 'homematic'

HA_HOMEMATIC_DEVICES = None
devices_not_registered = []

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
DISCOVER_THERMOSTATS = "homematic.thermostat"

ATTR_DISCOVER_DEVICES = "devices"
ATTR_DISCOVER_CONFIG = "config"

HM_DEVICE_TYPES = {
   DISCOVER_SWITCHES: ['HMSwitch'],
   DISCOVER_LIGHTS: ['HMDimmer'],
   DISCOVER_SENSORS: ['HMCcu'],
   DISCOVER_THERMOSTATS: ['HMThermostat'],
   DISCOVER_BINARY_SENSORS: ['HMRemote', 'HMDoorContact'],
   DISCOVER_ROLLERSHUTTER: ['HMRollerShutter']
}

_LOGGER = logging.getLogger(__name__)


# pylint: disable=unused-argument
def setup(hass, config):
    """Setup the Homematic component."""
    
    global homematic_devices, HOMEMATIC

    local_ip = config[DOMAIN].get(LOCAL_IP)
    local_port = config[DOMAIN].get(LOCAL_PORT)
    remote_ip = config[DOMAIN].get(REMOTE_IP)
    remote_port = config[DOMAIN].get(REMOTE_PORT)
    autodetect = str(config[DOMAIN].get(AUTODETECT, False)).upper() == 'TRUE'
    
    if local_ip is None or local_port is None or remote_ip is None or remote_port is None: 
        _LOGGER.error("Missing required configuration item %s, %s, %s or %s",
                     LOCAL_IP, LOCAL_PORT, REMOTE_IP, REMOTE_PORT)
        return

    # Only required because there is no access on created entities and I lack the knowledge on 
    # a better way how to make the devices variable accessible in all homematic components

    def system_callback_handler(src, *args):

        if src == 'newDevices':
            (interface_id, dev_descriptions) = args
            key_dict = {}
            # Get list of all keys of the devices (ignoring channels)
            for dev in dev_descriptions:
                key_dict[dev['ADDRESS'].split(':')[0]] = True
            # Connect devices already created in HA to pyhomematic and add remaining devices to list
            devices_not_created = []
            for dev in key_dict:
                try:
                    if dev in homematic_devices:
                        for channel in homematic_devices[dev]:
                            channel.connect_to_homematic()
                    else:
                        devices_not_created.append(dev)
                except Exception as err:
                    _LOGGER.error("Failed to setup device %s: %s" % (str(dev), str(err)))
            # If configuration allows auto detection of devices all devices not configured are added.         
            if autodetect and devices_not_created:
                for component_name, func_get_devices, discovery_type in (
                        ('switch', get_switches, DISCOVER_SWITCHES),
                        ('light', get_lights, DISCOVER_LIGHTS),
                        ('rollershutter', get_rollershutters, DISCOVER_ROLLERSHUTTER),
                        ('binary_sensor', get_binary_sensors, DISCOVER_BINARY_SENSORS),
                        ('sensor', get_sensors, DISCOVER_SENSORS),
                        ('thermostat', get_thermostats, DISCOVER_THERMOSTATS)):
                    # Get all devices of a specific type
                    found_devices = func_get_devices(devices_not_created)
                    
                    # Devices of this type are found they are setup in HA and a event is fired
                    if found_devices:
                        component = get_component(component_name)
                        config = {component.DOMAIN: found_devices}
            
                        # Ensure component is loaded
                        homeassistant.bootstrap.setup_component(hass, component.DOMAIN, config)
            
                        # Fire discovery event
                        hass.bus.fire(EVENT_PLATFORM_DISCOVERED, {
                                      ATTR_SERVICE: discovery_type,
                                      ATTR_DISCOVERED: {ATTR_DISCOVER_DEVICES: found_devices,
                                                        ATTR_DISCOVER_CONFIG: ''}}
                                      )
                for dev in devices_not_created:
                    if dev in homematic_devices:
                        homematic_devices[dev].connect_to_homematic()
    
    # Create server thread
    HOMEMATIC.create_server(local=local_ip,
                            localport=local_port,
                            remote=remote_ip,
                            remoteport=remote_port,
                            systemcallback=system_callback_handler,
                            interface_id='homeassistant')
    HOMEMATIC.start() # Start server thread, connect to homegear, initialize to receive events
    # while not pyhomematic.devices or pyhomematic._server.working:
    #     time.sleep(1)
    # print('Homematic Devices found: ', len(HOMEMATIC.devices))
    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, HOMEMATIC.stop) # Stops server when Homeassistant is shuting down
    hass.config.components.append(DOMAIN)
    
    # if not autodetect:
    #    return True

    return True


def get_switches(keys=None):
    return get_devices(HM_DEVICE_TYPES[DISCOVER_SWITCHES], keys)


def get_lights(keys=None):
    return get_devices(HM_DEVICE_TYPES[DISCOVER_LIGHTS], keys)


def get_rollershutters(keys=None):
    return get_devices(HM_DEVICE_TYPES[DISCOVER_ROLLERSHUTTER], keys)


def get_binary_sensors(keys=None):
    return get_devices(HM_DEVICE_TYPES[DISCOVER_BINARY_SENSORS], keys)


def get_sensors(keys=None):
    return get_devices(HM_DEVICE_TYPES[DISCOVER_SENSORS], keys)


def get_thermostats(keys=None):
    return get_devices(HM_DEVICE_TYPES[DISCOVER_THERMOSTATS], keys)


def get_devices(device_types, keys):
    global HOMEMATIC
    
    device_arr = []
    if not keys:
        keys = HOMEMATIC.devices
    for key in keys:
        if HOMEMATIC.devices[key].__class__.__name__ in device_types:
            ordered_device_dict = OrderedDict()
            ordered_device_dict['platform'] = 'homematic'
            ordered_device_dict['key'] = key
            ordered_device_dict['name'] = HOMEMATIC.devices[key].NAME
            device_arr.append(ordered_device_dict)
    return device_arr


def setup_hmdevice_entity_helper(HMDeviceType, config, add_callback_devices):
    global devices
    
    if pyhomematic.Server is None:
        _LOGGER.error('Error setting up Homematic Device: Homematic server not configured.')
        return False
    address = config.get('address', None)
    if address is None:
        _LOGGER.error("Error setting up Homematic Device '%s': 'address' missing in configuration." % address)
        return False
    new_device = HMDeviceType(config)
    if address not in homematic_devices:
        homematic_devices[address] = []
    homematic_devices[address].append(new_device)
    add_callback_devices([new_device])        
    return True


class HMDevice:
    def __init__(self, config):
        """Initialize generic HM device."""
        self._config = config
        self._address = config.get('address', None)
        self._name = config.get('name', None)
        if not self._name:
            self._name = self._address
        self._state = None
        self._hmdevice = None
        # TODO: Check if _is_connected can be replaced by the usage of _hmdevice
        self._is_connected = False        
        self._is_available = False
    
    def connect_to_homematic(self):
        global HOMEMATIC
        
        if self._address in HOMEMATIC.devices:
            self._hmdevice = HOMEMATIC.devices[self._address]
            self._is_connected = True
            self._is_available = not self._hmdevice.UNREACH

    @property
    def should_poll(self):
        """Returns False as Homematic states are pushed by the XML RPC Server"""
        return False
    
    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def assumed_state(self):
        """Return True if unable to access real state of the light."""
        return not self.available

    @property
    def available(self):
        """Return True if light is available."""
        return self._is_available
