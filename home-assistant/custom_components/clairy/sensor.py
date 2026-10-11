from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ClairySensor(manager, "temperature"),
            ClairySensor(manager, "humidity"),
            ClairySensor(manager, "air_quality"),
        ]
    )


class ClairySensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, manager, kind: str) -> None:
        self.manager = manager
        self.kind = kind
        self._attr_unique_id = f"clairy_local_{kind}"
        if kind == "temperature":
            self._attr_name = "Temperature"
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif kind == "humidity":
            self._attr_name = "Humidity"
            self._attr_device_class = SensorDeviceClass.HUMIDITY
            self._attr_native_unit_of_measurement = PERCENTAGE
        else:
            self._attr_name = "Air quality"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "clairy_local")},
            name="Clairy Natural Air Purifier",
            manufacturer="Clairy",
        )

    @property
    def available(self) -> bool:
        return self.manager.reading is not None

    @property
    def native_value(self):
        reading = self.manager.reading
        if reading is None:
            return None
        if self.kind == "temperature":
            return reading.temperature
        if self.kind == "humidity":
            return reading.humidity
        return reading.air_quality

    @property
    def extra_state_attributes(self):
        reading = self.manager.reading
        if reading is None:
            return {}
        attrs = {
            "source_ip": reading.source_ip,
            "last_received": reading.received.isoformat(),
        }
        if self.manager.serial:
            attrs["serial"] = self.manager.serial
        return attrs

    async def async_added_to_hass(self) -> None:
        @callback
        def update() -> None:
            self.async_write_ha_state()

        self.async_on_remove(self.manager.subscribe(update))
