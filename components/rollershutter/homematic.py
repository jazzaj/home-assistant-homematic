import logging

"""
The homematic custom rollershutter platform.

Configuration:

rollershutter:
  - platform: homematic
    address: '<Homematic address for device>' # e.g. 'JEQ0XXXXXXX'
    name: '<User defined name>'

"""
from homeassistant.const import (STATE_OPEN, STATE_CLOSED, STATE_UNKNOWN)
from homeassistant.components.rollershutter import RollershutterDevice
import homeassistant.components.homematic as homematic


_LOGGER = logging.getLogger(__name__)

# List of component names (string) your component depends upon.
DEPENDENCIES = ['homematic']

def setup_platform(hass, config, add_callback_devices, discovery_info=None):
    return homematic.setup_hmdevice_entity_helper(HMRollershutter, config, add_callback_devices)


class HMRollershutter(homematic.HMDevice, RollershutterDevice):
    """Represents an Homematic Rollershutter in Home Assistant."""
    
    @property
    def current_position(self):
        """Return current position of roller shutter.
        None is unknown, 0 is closed, 100 is fully open.
        """
        if self._is_connected:
            return int((1 - self._level) * 100)
        else:
            return None
        
    def set_position(self, position):
        """Move the roller shutter to a defined position between 0 (closed) and 100 (fully open)"""
        if self._is_connected:
            position = min(100, max(0, position))
            self._hmdevice.level = (100 - position) / 100.0

    @property
    def state(self):
        """Return the state of the roller shutter."""
        current = self.current_position

        if current is None:
            return STATE_UNKNOWN

        return STATE_CLOSED if current == 100 else STATE_OPEN

    def move_up(self, **kwargs):
        """Move the roller shutter up."""
        if self._is_connected:
            self._hmdevice.move_up()

    def move_down(self, **kwargs):
        """Move the roller shutter down."""
        if self._is_connected:
            self._hmdevice.move_down()

    def stop(self, **kwargs):
        """Stop the device."""
        if self._is_connected:
            self._hmdevice.stop()

    def connect_to_homematic(self):
        """Configuration specific to device after connection with pyhomematic is established"""
        def event_received(device, caller, attribute, value):
            attribute = str(attribute).upper()
            if attribute == 'LEVEL':
                self._level = float(value)
            elif attribute == 'UNREACH':
                self._is_available = not bool(value)
            else:
                return
            self.update_ha_state()

        super().connect_to_homematic()
        if self._is_available:
            self._hmdevice.setEventCallback(event_received)
            self._level = self._hmdevice.level
            self.update_ha_state()
    
    # TODO: For testing purposes only. To be deleted...
    # @property
    # def state_attributes(self):
    #     data = super(HMRollershutter, self).state_attributes
        #data['Test'] = 50
    #     return data
