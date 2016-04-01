import logging

"""
The homematic custom light platform.

Configuration:

switch:
  - platform: homematic
    key: '<Homematic key for device>' # e.g. 'JEQ0XXXXXXX'
    name: '<User defined name>'

"""

from homeassistant.components.switch import SwitchDevice
from homeassistant.const import (STATE_ON, STATE_OFF)

_LOGGER = logging.getLogger(__name__)

# List of component names (string) your component depends upon.
DEPENDENCIES = ['homematic']
REQUIREMENTS = ['pyhomematic']

import pyhomematic
#import homematic as pyhomematic

HOMEMATIC = pyhomematic

def setup_platform(hass, config, add_callback_devices, discovery_info=None):
    if HOMEMATIC.Server is None:
        _LOGGER.error('Homematic server not initialized')
        return False
    key = config.get('key', None)
    name = config.get("name", None)
    if key is None:
        _LOGGER.warning('Homematic switch: Key missing in configuration file')
        return False
    add_callback_devices([HMSwitch(key, name)])
    return True


class HMSwitch(SwitchDevice):
    """Represents an Homematic Switch in Home Assistant."""
    
    def __init__(self, key, name):
        """Initialize an Homematic Switch."""
        self._key = key
        self._name = name
        
        def event_received(device, caller, attribute, value):
            attribute = str(attribute).upper()
            if attribute == 'STATE':
                self._state = bool(value)
            elif attribute == 'UNREACH':
                self._is_available = not bool(value)
            else:
                return
            self.update_ha_state()
            
        HOMEMATIC.devices[self._key].setEventCallback(event_received)
        self._state = HOMEMATIC.devices[self._key].is_on
        self._is_available = self._check_availability()
        
    @property
    def should_poll(self):
        """Return True if entity has to be polled for state.
        False if entity pushes its state to HA.
        """
        return False
    
    @property
    def name(self):
        """Return the name of the switch."""
        return self._name
    
    @property
    def is_on(self):
        """Return True if switch is on."""
        return self._state

    @property
    def assumed_state(self):
        """Return True if unable to access real state of the switch."""
        return not self.available

    @property
    def available(self):
        """Return True if switch is available."""
        return self._is_available
        
    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._state = True
        HOMEMATIC.devices[self._key].on()

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self._state = False
        HOMEMATIC.devices[self._key].off()

    def _check_availability(self):
        """ Test if device is available. Only required at startup as later the availabilty will be tracked by monitoring events."""
        # TODO: Missing/unknow functionality in pyhomematic
        return True
