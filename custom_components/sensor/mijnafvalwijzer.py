"""
@ Authors     : Bram van Dartel
@ Date        : 18/04/2018
@ Version     : 1.0.5
@ Description : MijnAfvalwijzer Sensor - It queries mijnafvalwijzer.nl.
"""
<<<<<<< HEAD
=======

>>>>>>> 87cbd0f6df8cbd6068360b447af484c967e4f682
from datetime import datetime, timedelta
import voluptuous as vol
import requests
import asyncio
import logging

from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'MijnAfvalwijzer Sensor'
ICON = 'mdi:delete-empty'
SENSOR_PREFIX = 'trash_'
CONST_POSTCODE = "postcode"
CONST_HUISNUMMER = "huisnummer"
CONST_TOEVOEGING = "toevoeging"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONST_POSTCODE): cv.string,
    vol.Required(CONST_HUISNUMMER): cv.string,
    vol.Optional(CONST_TOEVOEGING, default=""): cv.string,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Setup the sensor platform."""
    postcode = config.get(CONST_POSTCODE)
    huisnummer = config.get(CONST_HUISNUMMER)
    toevoeging = config.get(CONST_TOEVOEGING)
    url = ("http://json.mijnafvalwijzer.nl/?method=postcodecheck& \
            postcode={0}&street=&huisnummer={1}&toevoeging={2}& \
            platform=phone&langs=nl&").format(postcode, huisnummer, toevoeging)
    response = requests.get(url)
    json_obj = response.json()
    json_data = json_obj['data']['ophaaldagen']['data']
    json_data_next = json_obj['data']['ophaaldagenNext']['data']
    today = datetime.today().strftime("%Y-%m-%d")
    dateConvert = datetime.strptime(today, "%Y-%m-%d") + timedelta(days=1)
    tomorrow = datetime.strftime(dateConvert, "%Y-%m-%d")
    trashTotal = [{1: 'today'}, {2: 'tomorrow'}]
    trashType = {}
    countType = 3
    devices = []

    # Collect trash items
    for item in json_data or json_data_next:
        name = item["nameType"]
        if name not in trashType:
                trash = {}
                trashType[name] = item["nameType"]
                trash[countType] = item["nameType"]
                countType += 1
                trashTotal.append(trash)

    data = (TrashCollectionSchedule(json_data, json_data_next,
            today, tomorrow, trashTotal))

    for trash_type in trashTotal:
        for t in trash_type.values():
            devices.append(TrashCollectionSensor(t, data))
    async_add_devices(devices, True)


class TrashCollectionSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, data):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self.data = data

    @property
    def name(self):
        """Return the name of the sensor."""
        return SENSOR_PREFIX + self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Set the default sensor icon."""
        return ICON

    def update(self):
        """Fetch new state data for the sensor."""
        self.data.update()
        for d in self.data.data:
            if d['name_type'] == self._name:
                self._state = d['pickup_date']


class TrashCollectionSchedule(object):
    """Fetch new state data for the sensor."""

    def __init__(self, json_data, json_data_next, today, tomorrow, trashTotal):
        """Fetch vars."""
        self._json_data = json_data
        self._json_data_next = json_data_next
        self._today = today
        self._tomorrow = tomorrow
        self._trashTotal = trashTotal
        self.data = None

    def update(self):
        """Fetch new state data for the sensor."""
        json_data = self._json_data
        json_data_next = self._json_data_next
        today = self._today
        tomorrow = self._tomorrow
        trashTotal = self._trashTotal
        trashType = {}
        tschedule = []

        # Collect upcoming trash pickup dates
        for name in trashTotal:
            for item in json_data or json_data_next:
                name = item["nameType"]
                dateFormat = datetime.strptime(item['date'], "%Y-%m-%d")
                dateConvert = dateFormat.strftime("%Y-%m-%d")
                if name not in trashType:
                    if item['date'] >= today:
                        trash = {}
                        trashType[name] = item["nameType"]
                        trash['name_type'] = item['nameType']
                        trash['pickup_date'] = dateConvert
                        tschedule.append(trash)
                        self.data = tschedule
                    if item['date'] == today:
                        trash = {}
                        trashType[name] = "today"
                        trash['name_type'] = "today"
                        trash['pickup_date'] = item['nameType']
                        tschedule.append(trash)
                        self.data = tschedule
                    if item['date'] == tomorrow:
                        trash = {}
                        trashType[name] = "tomorrow"
                        trash['name_type'] = "tomorrow"
                        trash['pickup_date'] = item['nameType']
                        tschedule.append(trash)
                        self.data = tschedule
