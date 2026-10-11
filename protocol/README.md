# Clairy local UDP protocol

This document describes the local read path recovered from the first-generation Clairy Android application and used by the Clairy Local project.

## Transport

- IPv4 UDP
- Local port: `6666`
- Multicast group: `239.0.0.1`
- Listener binds to UDP `6666` and joins the multicast group on the LAN interface.
- Commands to a known purifier are sent by unicast to the purifier's IP on port `6666`, using the same socket bound to `6666`.

No TCP, HTTP, DNS, cloud account, authentication token, BLE handshake or encryption is required for the local sensor read path.

## Current measurements

Current measurements arrive as unsolicited packets with opcode `1` (`DISCOVERY`). No active LAN command has been identified that is proven to request an immediate sensor measurement; a persistent listener should therefore be used.

The receiver requires at least 19 bytes. Fields used by the original application are:

| Offset | Size | Meaning |
| --- | --- | --- |
| 5 | 1 | opcode; `1` = discovery/current reading |
| 8-9 | 2 | temperature, unsigned little-endian, divide by 10 for °C |
| 10-11 | 2 | relative humidity, unsigned little-endian, divide by 10 for % |
| 12-13 | 2 | Clairy air-quality/IAQ value, unsigned little-endian, divide by 10 |
| 14 | 1 | fan state; non-zero = on |
| 15 | 1 | raw fan-speed byte |

The air-quality field is the application's `ClairyModel.quality` value. It is **not a raw VOC concentration** and should not be labelled as ppb, ppm or mg/m³.

## Identity

The exact `GET_ID` request observed in the application is:

```text
02 09 00 ff ff 0c 00 00 02 13 03
```

An identity response uses opcode `13` at offset 5 and is at least 15 bytes long. Offsets 8-11 contain an unsigned little-endian 32-bit serial number. The original application renders it as a minimum of nine digits, zero padded.

`GET_ID` retrieves identity. It is not known to trigger a fresh sensor reading.

## Home Assistant / containers

A Home Assistant integration should keep a persistent UDP listener rather than repeatedly opening a polling socket. UDP port `6666` and multicast traffic must be able to reach the listener. Container or VM networking that isolates multicast can prevent discovery.

## Verification status

The packet decoder and reader have been exercised with synthetic packets. The local Android modification and LAN communication have also been used with original Clairy hardware. Some envelope bytes and the exact firmware transmission cadence remain undocumented.
