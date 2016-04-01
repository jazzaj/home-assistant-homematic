import logging

"""
The homematic custom rollershutter platform.

Configuration:

rollershutter:
  - platform: homematic
    key: '<Homematic key for device>' # e.g. 'JEQ0XXXXXXX'
    name: '<User defined name>'

"""

from homeassistant.components.rollershutter import RollershutterDevice 
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
        _LOGGER.warning('Homematic rollershutter: Key missing in configuration file')
        return False
    add_callback_devices([HMRollershutter(key, name)])
    return True


class HMRollershutter(RollershutterDevice):
    """Represents an Homematic Rollershutter in Home Assistant."""
    
    def __init__(self, key, name):
        """Initialize an Homematic Rollershutter."""
        self._key = key # TODO: Maybe not required and can be replaced by entity_id (previous line)
        self._name = name
        self._level = HOMEMATIC.devices[self._key].level
        
        def event_received(device, caller, attribute, value):
            attribute = str(attribute).upper()
            if attribute == 'LEVEL':
                self._level = float(value)
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
    def current_position(self):
        """Return current position of roller shutter.
        None is unknown, 0 is closed, 100 is fully open.
        """
        return int(self._level * 100)
    
    def move_up(self, **kwargs):
        """Move the roller shutter up."""
        print(kwargs)
        HOMEMATIC.devices[self._key].move_up()

    def move_down(self, **kwargs):
        """Move the roller shutter down."""
        print(kwargs)
        HOMEMATIC.devices[self._key].move_down()

    def stop(self, **kwargs):
        """Stop the device."""
        print(kwargs)
        HOMEMATIC.devices[self._key].stop()
        
    @property
    def available(self):
        """Return True if light is available."""
        return self._is_available

    def _check_availability(self):
        """ Test if device is available. Only required at startup as later the availabilty will be tracked by monitoring events."""
        # TODO: Missing/unknow functionality in pyhomematic
        return True
