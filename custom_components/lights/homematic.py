import logging

"""
The homematic custom switch platform.

Configuration:

# TODO

"""

from homeassistant.components.light import (ATTR_BRIGHTNESS, Light)

_LOGGER = logging.getLogger(__name__)

# List of component names (string) your component depends upon.
DEPENDENCIES = ['homematic']

REQUIREMENTS = ['pyhomematic']

import pyhomematic

HOMEMATIC = pyhomematic

# TODO:
Implement callbacks for all devices --> If light is switched out by remote/switch home assistant should know...

def setup_platform(hass, config, add_devices, discovery_info=None):
    if HOMEMATIC.Server is None:
        _LOGGER.error('Homematic server not initialized')
        return False
    key = config.get('key', None)
    name = config.get("name", None)
    dimmer = str(config.get("dimmer", False)).upper() == "TRUE"
    if key is None:
        _LOGGER.warning('Homematic light: Key missing in configuration file')
        return False
    add_devices([HMLight(key, name, dimmer)])
    return True


class HMLight(Light):
    """Represents an Homematic Switch in Home Assistant."""
    
    def __init__(self, key, name, dimmer):
        """Initialize an Homematic Light."""
        self._key = key
        self._name = name
        self._dimmer = dimmer
        if not hasattr(HOMEMATIC.devices[self._key], 'level'):
            self._dimmer = False
        self._is_available = True
        
    @property
    def name(self):
        """Return the hostname of the server."""
        return self._name
    
    @property
    def brightness(self):
        """Return the brightness of this light between 0..1"""
        if self._dimmer:
            return int(HOMEMATIC.devices[self._key].level*255)
        else:
            if self.is_on:
                return 255
            else:
                return 0
    
    @property
    def is_on(self):
        """Return True if entity is on."""
        if self._dimmer:
            return HOMEMATIC.devices[self._key].level > 0
        else:
            return HOMEMATIC.devices[self._key].is_on

    def turn_on(self, **kwargs):
        """Turn the entity on."""
        if ATTR_BRIGHTNESS in kwargs and self._dimmer:
            percent_bright = float(kwargs[ATTR_BRIGHTNESS]) / 255
            HOMEMATIC.devices[self._key].level = percent_bright
        else:
            HOMEMATIC.devices[self._key].on()            

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        HOMEMATIC.devices[self._key].off()
