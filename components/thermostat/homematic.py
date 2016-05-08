import logging

"""
The Homematic thermostat platform.

Configuration:

thermostat:
  - platform: homematic
    address: '<Homematic address for device>' # e.g. 'JEQ0XXXXXXX'
    name: '<User defined name>'

"""
# List of component names (string) your component depends upon.
DEPENDENCIES = ['homematic']

import homeassistant.components.homematic as homematic
from homeassistant.components.thermostat import ThermostatDevice
from homeassistant.helpers.temperature import convert
from homeassistant.const import TEMP_CELSIUS

PROPERTY_VALVE_STATE = 'VALVE_STATE'
PROPERTY_CONTROL_MODE = 'CONTROL_MODE'

HMCOMP = 0
MAXCOMP = 1
VARIANTS = {
    "HM-CC-RT-DN" : HMCOMP,
    "HM-CC-RT-DN-BoM" : HMCOMP,
    "BC-RT-TRX-CyG" : MAXCOMP,
    "BC-RT-TRX-CyG-2" : MAXCOMP,
    "BC-RT-TRX-CyG-3" : MAXCOMP,
    "BC-RT-TRX-CyG-4" : MAXCOMP
}

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_callback_devices, discovery_info=None):
    return homematic.setup_hmdevice_entity_helper(HMThermostat, config, add_callback_devices)


class HMThermostat(homematic.HMDevice, ThermostatDevice):
    """Represents an Homematic Thermostat in Home Assistant."""

    def __init__(self, config):
        super().__init__(config)
        self._battery = None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement that is used."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._is_connected:
            try:
                return self._current_temperature
            except Exception as err:
                _LOGGER.error("Exception getting current temperature: %s" % str(err))
        else:
            return None

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self._is_connected:
            try:
                return self._set_temperature
            except Exception as err:
                _LOGGER.error("Exception getting set temperature: %s" % str(err))
        else:
            return None

    def set_temperature(self, temperature):
        """Set new target temperature."""
        if self._is_connected:
            try:
                self._hmdevice.set_temperature = temperature
            except Exception as err:
                _LOGGER.error("Exception setting temperature: %s" % str(err))

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        _LOGGER.info("device_state_attributes")
        if self._is_connected:
            return {"valve": self._valve,
                    "battery": self._battery,
                    "mode": self._mode}
        else:
            return {"valve": None,
                    "battery": None,
                    "mode": None}

    @property
    def min_temp(self):
        """Return the minimum temperature - 4.5 means off."""
        return convert(4.5, TEMP_CELSIUS, self.unit_of_measurement)

    @property
    def max_temp(self):
        """Return the maximum temperature - 30.5 means on."""
        return convert(30.5, TEMP_CELSIUS, self.unit_of_measurement)

    def connect_to_homematic(self):
        """Configuration specific to device after connection with pyhomematic is established"""
        def event_received(device, caller, attribute, value):
            attribute = str(attribute).upper()
            if attribute == 'SET_TEMPERATURE':
                self._set_temperature = value
            elif attribute == 'ACTUAL_TEMPERATURE':
                self._current_temperature = value
            elif attribute == 'VALVE_STATE':
                self._valve = float(value)
            elif attribute == 'CONTROL_MODE':
                self._mode = value
            elif attribute == 'BATTERY_STATE':
                if isinstance(value, float):
                    self._battery = value
            elif attribute == 'LOWBAT':
                if value:
                    self._battery = 1.5
                else:
                    self._battery = 4.6
            elif attribute == 'UNREACH':
                self._is_available = not bool(value)
            else:
                return
            self.update_ha_state()

        super().connect_to_homematic()
        if self._is_available:
            try:
                self._hmdevice.setEventCallback(event_received)
                self._current_temperature = self._hmdevice.actual_temperature
                self._set_temperature = self._hmdevice.set_temperature
                self._battery = None
                if self._hmdevice._TYPE in VARIANTS:
                    if VARIANTS[self._hmdevice._TYPE] == HMCOMP:
                        self._battery = self._hmdevice.battery_state
                    elif VARIANTS[self._hmdevice._TYPE] == MAXCOMP:
                        if self._hmdevice.battery_state:
                            self._battery = 1.5
                        else:
                            self._battery = 4.6
                self._valve = None
                self._mode = None
                self.update_ha_state()
            except Exception as err:
                _LOGGER.error("Exception while connecting: %s" % str(err))

