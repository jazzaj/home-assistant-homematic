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
    add_devices([HMLight(key, name, dimmer, hass)])
    return True


class HMLight(Light):
    """Represents an Homematic Switch in Home Assistant."""
    
    def __init__(self, key, name, dimmer, hass):
        """Initialize an Homematic Light."""
		self.entity_id = key
        self._key = key # TODO: Maybe not required and can be replaced by entity_id (previous line)
        self._name = name
        self._dimmer = dimmer
        self._hass = hass
        if not hasattr(HOMEMATIC.devices[self._key], 'level'):
            self._dimmer = False
        self._is_available = True
        HOMEMATIC.devices[self._key].set_state_changed_callback(homematic_changed_state)
        
    @property
    def should_poll(self):
        """Return True if entity has to be polled for state.
        False if entity pushes its state to HA.
        """
		# TODO: Check if this is required after callback logic is implemented
        return True
	
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
			
	@property
    def assumed_state(self):
        """Return True if unable to access real state of the entity."""
		# TODO: Return True if homematic has communication issues with the device.
        return False
		
	@property
    def available(self):
        """Return True if entity is available."""
		# TODO: Return False if homematic has communication issues with the device.
        return True
		
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
        
    def homematic_changed_state(self, hm_new_state):
        # TODO: Convert homematic new_state to HASS new state
		hass_new_state = {
            "last_updated": now,
            "state": "on",
            "entity_id": e_id,
            "attributes": {},
            "last_changed": now
        }
        self._hass.states.set(self.entity_id, hass_new_state, attributes=None)
