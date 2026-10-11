# Home Assistant integration

This custom integration listens directly for first-generation Clairy UDP broadcasts on the local network. It does not use the abandoned Clairy cloud service.

## Exposed sensors

- Temperature (°C)
- Relative humidity (%)
- Air quality / IAQ (unitless Clairy quality score)

The air-quality entity is intentionally not labelled as VOC concentration because the protocol exposes the application's calculated quality value rather than raw VOC concentration.

## Installation

Copy `custom_components/clairy` into your Home Assistant configuration directory so the resulting path is:

```text
/config/custom_components/clairy/
```

Restart Home Assistant, then go to **Settings → Devices & services → Add integration → Clairy**.

There is no cloud account, password or API key. The integration listens on UDP port `6666` and joins multicast group `239.0.0.1`.

If the entities remain unavailable, check that multicast traffic from the Clairy can reach the Home Assistant host/VM/container. Client isolation, VLAN rules and some container network modes can block multicast.

## Status

The integration is currently intended for a single Clairy. Multi-device handling can be added once it has been tested with multiple physical units.
