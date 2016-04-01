import logging

"""
The homematic custom light platform.
Will also work with switches.

Configuration:

light:
  - platform: homematic
    key: '<Homematic key for device>' # e.g. 'JEQ0XXXXXXX'
    name: '<User defined name>'

"""

from homeassistant.components.light import (ATTR_BRIGHTNESS, Light)
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
        _LOGGER.warning('Homematic light: Key missing in configuration file')
        return False
    add_callback_devices([HMLight(key, name)])
    return True


class HMLight(Light):
    """Represents an Homematic Switch in Home Assistant."""
    
    def __init__(self, key, name):
        """Initialize an Homematic Light."""
        self._key = key
        self._name = name
        if hasattr(HOMEMATIC.devices[self._key], 'level'):
            self._dimmer = True 
            self._level = HOMEMATIC.devices[self._key].level
        else:
            self._dimmer = False 
            self._state = HOMEMATIC.devices[self._key].is_on
        
        def event_received(device, caller, attribute, value):
            attribute = str(attribute).upper()
            if attribute == 'LEVEL':
                self._level = float(value)
            elif attribute == 'STATE':
                self._state = bool(value)
            elif attribute == 'UNREACH':
                self._is_available = not bool(value)
            else:
                return
            self.update_ha_state()
            
        HOMEMATIC.devices[self._key].setEventCallback(event_received)
        self._is_available = self._check_availability()
        
    @property
    def should_poll(self):
        """Return True if entity has to be polled for state.
        False if entity pushes its state to HA.
        """
        return False
    
    @property
    def name(self):
        """Return the name of the light."""
        return self._name
    
    @property
    def brightness(self):
        """Return the brightness of this light between 0..255"""
        if self._dimmer:
            return int(self._level * 255)
        else:
            return None
    
    @property
    def is_on(self):
        """Return True if light is on."""
        if self._dimmer:
            return self._level > 0
        else:
            return self._state

    @property
    def assumed_state(self):
        """Return True if unable to access real state of the light."""
        return not self.available
        
    @property
    def available(self):
        """Return True if light is available."""
        return self._is_available
        
    def turn_on(self, **kwargs):
        """Turn the light on."""
        if ATTR_BRIGHTNESS in kwargs and self._dimmer:
            percent_bright = float(kwargs[ATTR_BRIGHTNESS]) / 255
            HOMEMATIC.devices[self._key].level = percent_bright
        else:
            self._state = True
            HOMEMATIC.devices[self._key].on()

    def turn_off(self, **kwargs):
        """Turn the light off."""
        if not self._dimmer:
            self._state = False
        HOMEMATIC.devices[self._key].off()

    def _check_availability(self):
        """ Test if device is available. Only required at startup as later the availabilty will be tracked by monitoring events."""
        # TODO: Missing/unknow functionality in pyhomematic
        return True
