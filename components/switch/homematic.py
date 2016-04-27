import logging

"""
The homematic custom light platform.

Configuration:

switch:
  - platform: homematic
    address: '<Homematic address for device>' # e.g. 'JEQ0XXXXXXX'
    name: '<User defined name>'

"""

from homeassistant.components.switch import SwitchDevice
import homeassistant.components.homematic as homematic

_LOGGER = logging.getLogger(__name__)

# List of component names (string) your component depends upon.
DEPENDENCIES = ['homematic']

def setup_platform(hass, config, add_callback_devices, discovery_info=None):
    return homematic.setup_pyhomematic_entity_helper(HMSwitch, config, add_callback_devices)


class HMSwitch(homematic.HMDevice, SwitchDevice):
    """Represents an Homematic Switch in Home Assistant."""
            
    @property
    def is_on(self):
        """Return True if switch is on."""
        return self._state

    @property
    def assumed_state(self):
        """Return True if unable to access real state of the switch."""
        return not self.available

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        if self._is_connected:
            self._pyhomematic.on()
            self._state = True

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        if self._is_connected:
            self._pyhomematic.off()
            self._state = False

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
