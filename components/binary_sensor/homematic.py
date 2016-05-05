import logging

"""
The homematic binary sensor platform.

Configuration:

switch:
  - platform: homematic
    address: '<Homematic address for device>' # e.g. 'JEQ0XXXXXXX'
    name: '<User defined name>'

"""

from homeassistant.components.binary_sensor import BinarySensorDevice
import homeassistant.components.homematic as homematic

_LOGGER = logging.getLogger(__name__)

# List of component names (string) your component depends upon.
DEPENDENCIES = ['homematic']

SENSOR_TYPES = {
    "opened": "opening",
    "brightness": "light",
    "vibration": "vibration",
    "loudness": "sound"
}

def setup_platform(hass, config, add_callback_devices, discovery_info=None):
    return homematic.setup_hmdevice_entity_helper(HMBinarySensor, config, add_callback_devices)


class HMBinarySensor(homematic.HMDevice, BinarySensorDevice):
    """Represents diverse binary Homematic units in Home Assistant."""
    def __init__(self, config):
        super().__init__(config)
        self._sensor_class = None
    
    @property
    def is_on(self):
        """Return True if switch is on."""
        return self._state

    @property
    def sensor_class(self):
        """Return the class of this sensor, from SENSOR_CLASSES."""
        return self._sensor_class

    @property
    def state_attributes(self):
        """Return device specific state attributes."""
        attr = {}

        if self.sensor_class is not None:
            attr['sensor_class'] = self.sensor_class

        return attr

    def connect_to_homematic(self):
        """Configuration specific to device after connection with pyhomematic is established"""
        super().connect_to_homematic()
        if type(self._hmdevice).__name__ == "HMDoorContact":
            self._sensor_class = 'opening'
            if self._is_available:
                self._state = self._hmdevice.state
        if type(self._hmdevice).__name__ == "HMRemote":
            self._sensor_class = 'remote button'
            self._channel = self._config.get('channel', None)
            if not self._channel:
                _LOGGER.error("No channel defined for '%s'" %self._address)
                self._is_available = False
        if self._is_available:
            self.update_ha_state()