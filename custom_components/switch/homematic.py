import logging

"""
The homematic custom switch platform.

Configuration:

# TODO

"""

from homeassistant.components.switch import SwitchDevice
from homeassistant.components.light import Light

_LOGGER = logging.getLogger(__name__)

# List of component names (string) your component depends upon.
DEPENDENCIES = ['homematic']

REQUIREMENTS = ['pyhomematic']

import pyhomematic

HOMEMATIC = pyhomematic

def setup_platform(hass, config, add_devices, discovery_info=None):
    if HOMEMATIC.Server is None:
        _LOGGER.error('Homematic server not initialized')
        return False
    add_devices([HMSwitch('JEQ0696937')])
    return True


class HMSwitch(SwitchDevice):
    """Represents an Homematic Switch in Home Assistant."""
    
    def __init__(self, key):
        """Initialize an Homematic Switch."""
        self._key = key
        
    @property
    def is_on(self):
        """Return True if entity is on."""
        return HOMEMATIC.devices[self._key].is_on

    def turn_on(self, **kwargs):
        """Turn the entity on."""
        HOMEMATIC.devices[self._key].on()

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        HOMEMATIC.devices[self._key].off()
