import logging

"""
The homematic binary sensor platform.

Configuration:

switch:
  - platform: homematic
    address: '<Homematic address for device>' # e.g. 'JEQ0XXXXXXX'
    name: '<User defined name>'

"""

from homeassistant.const import (STATE_CLOSED, STATE_OPEN, STATE_OFF, STATE_ON, STATE_UNKNOWN)
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
        self._battery = STATE_UNKNOWN
        self._rssi = STATE_UNKNOWN
        self._sabotage = STATE_UNKNOWN
    
    @property
    def is_on(self):
        """Return True if switch is on."""
        return self._state

    @property
    def sensor_class(self):
        """Return the class of this sensor, from SENSOR_CLASSES."""
        return self._sensor_class

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        attributes = {"sensor_class" : self.sensor_class,
                      "rssi" : self._rssi,
                      "sabotage" : self._sabotage}
        if self._battery:
            attributes['battery'] = self._battery

        return attributes

    def connect_to_homematic(self):
        """Configuration specific to device after connection with pyhomematic is established"""
        def event_received(device, caller, attribute, value):
            attribute = str(attribute).upper()
            if attribute == 'STATE':
                self._state = bool(value)
            elif attribute == 'LOWBAT':
                if value:
                    self._battery = 1.5
                else:
                    self._battery = 4.6
            elif attribute == 'PRESS_LONG_RELEASE':
                if int(device.split(':')[1]) == int(self._button):
                        self._state = 0
            elif attribute == 'PRESS_SHORT' or attribute == 'PRESS_LONG':
                if int(device.split(':')[1]) == int(self._button):
                    self._state = 1
                    self.update_ha_state()
                    self._state = 0
            elif attribute == 'RSSI_DEVICE':
                self._rssi = value
            elif attribute == 'ERROR':
                if value == 7:
                    self._sabotage = True
                else:
                    self._sabotage = False
            elif attribute == 'UNREACH':
                self._is_available = not bool(value)
            else:
                return
            self.update_ha_state()

        super().connect_to_homematic()

        if type(self._hmdevice).__name__ == "HMDoorContact":
            _LOGGER.debug("Setting up HMDoorContact %s" % self._hmdevice._ADDRESS)
            self._sensor_class = 'opening'
            if self._is_available:
                self._state = self._hmdevice.state
        elif type(self._hmdevice).__name__ == "HMRemote":
            _LOGGER.debug("Setting up HMRemote %s" % self._hmdevice._ADDRESS)
            self._sensor_class = 'remote button'
            self._button = self._config.get('button', None)
            if not self._button:
                _LOGGER.error("No button defined for '%s'" %self._address)
                self._is_available = False
        else:
            self._sensor_class = None
            self._state = None
        if self._is_available:
            self._hmdevice.setEventCallback(event_received)
            self.update_ha_state()
