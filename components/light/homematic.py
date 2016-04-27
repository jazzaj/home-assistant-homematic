import logging

"""
The homematic custom light platform.
Will also work with switches.

Configuration:

light:
  - platform: homematic
    addresss: '<Homematic addresss for device>' # e.g. 'JEQ0XXXXXXX'
    name: '<User defined name>'

"""

from homeassistant.components.light import (ATTR_BRIGHTNESS, Light)
import homeassistant.components.homematic as homematic

_LOGGER = logging.getLogger(__name__)

# List of component names (string) your component depends upon.
DEPENDENCIES = ['homematic']

def setup_platform(hass, config, add_callback_devices, discovery_info=None):
    return homematic.setup_pyhomematic_entity_helper(HMLight, config, add_callback_devices)

class HMLight(homematic.HMDevice, Light):
    """Represents an Homematic Light in Home Assistant."""
            
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
        if self._is_connected:
            if self._dimmer:
                return self._level > 0
            else:
                return self._state
        else:
            return False
        
    def turn_on(self, **kwargs):
        """Turn the light on."""
        if self._is_connected:
            if ATTR_BRIGHTNESS in kwargs and self._dimmer:
                percent_bright = float(kwargs[ATTR_BRIGHTNESS]) / 255
                self._pyhomematic.level = percent_bright
            else:
                self._state = True
                self._pyhomematic.on()

    def turn_off(self, **kwargs):
        """Turn the light off."""
        if self._is_connected:
            if not self._dimmer:
                self._state = False
            self._pyhomematic.off()
            
    def connect_to_homematic(self):
        """Configuration specific to device after connection with pyhomematic is established"""
        super().connect_to_homematic()
        if hasattr(self._pyhomematic, 'level'):
            self._dimmer = True 
        else:
            self._dimmer = False 
        if self._is_available:
            if self._dimmer:
                self._level = self._pyhomematic.level
            else:
                self._state = self._pyhomematic.is_on
            self.update_ha_state()
