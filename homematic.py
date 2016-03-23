"""
Support for Homematic Devices.
"""
import logging

from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP
from homeassistant.loader import get_component
from homeassistant.helpers import validate_config
from homeassistant.helpers.entity import ToggleEntity

REQUIREMENTS = ['pyhomematic']
DOMAIN = 'homematic'

HOMEMATIC = None

LOCAL_IP = "LOCAL_IP"
LOCAL_PORT = "LOCAL_PORT"

DISCOVER_SWITCHES = "homematic.switches"
DISCOVER_SENSORS = "homematic.sensors"
DISCOVER_BINARY_SENSORS = "homematic.binary_sensors"
DISCOVER_ROLLERSHUTTER = "homematic.rollershutter"


# pylint: disable=unused-argument
def setup(hass, config):
    """Setup the Homematic component."""

	def homematic_callback(source, *args):
		""" """
		# TODO: Add callbacks
		pass
		
		
    global HOMEMATIC

    logger = logging.getLogger(__name__)
    local_ip = config[DOMAIN].get(LOCAL_IP)
	local_port = config[DOMAIN].get(LOCAL_PORT)

    if local_ip is None or local_port is None: 
        logger.error("Missing required configuration item %s or %s",
                     LOCAL_IP, LOCAL_PORT)
        return

    import homematic
	
	homematic.create_server(local=LOCAL_IP, localport=LOCAL_PORT, remote=None, remoteport=None, systemcallback=syscb) # Create server thread
	homematic.start() # Start server thread, connect to homegear, initialize to receive events
	hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, homematic.stop) # Stops server when Homeassistant is shuting down
	# TODO: Query server for all devices?
    HOMEMATIC = homematic

	for component_name, func_exists, discovery_type in (
		('switch', homematic.get_switches, DISCOVER_SWITCHES),
		('rollershutter', homematic.get_rollershutters, DISCOVER_ROLLERSHUTTER),
		('binary_sensor', homematic.get_remote_channels, DISCOVER_BINARY_SENSORS),
		('sensor', homematic.get_thermostats, DISCOVER_SENSORS)
		)

		if func_exists():
			component = get_component(component_name) 

			# Ensure component is loaded
			bootstrap.setup_component(hass, component.DOMAIN, config)

			# Fire discovery event
			hass.bus.fire(EVENT_PLATFORM_DISCOVERED, {
				ATTR_SERVICE: discovery_type,
				ATTR_DISCOVERED: {}
			})

	return True

	