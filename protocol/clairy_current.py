#!/usr/bin/env python3
"""Read current measurements broadcast by a first-generation Clairy."""

import argparse
import datetime as dt
import json
import socket
import struct

GROUP = "239.0.0.1"
PORT = 6666
GET_ID = bytes.fromhex("02 09 00 ff ff 0c 00 00 02 13 03")


def decode(data: bytes):
    """Decode the packet types needed for identity and current readings."""
    if len(data) >= 15 and data[5] == 13:
        serial = struct.unpack_from("<I", data, 8)[0]
        return {"type": "identity", "serial": f"{serial:09d}"}

    if len(data) >= 19 and data[5] == 1:
        temperature, humidity, quality, fan, speed = struct.unpack_from(
            "<HHHBB", data, 8
        )
        return {
            "type": "reading",
            "temperature_c": temperature / 10.0,
            "humidity_percent": humidity / 10.0,
            "air_quality": quality / 10.0,
            "fan_on": bool(fan),
            "fan_speed_raw": speed,
            "received_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "raw_hex": data.hex(),
        }

    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interface",
        default="0.0.0.0",
        help="IPv4 address of the LAN interface used to join multicast",
    )
    parser.add_argument(
        "--ip",
        help="Known Clairy IPv4 address; sends GET_ID to this address",
    )
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PORT))
    membership = socket.inet_aton(GROUP) + socket.inet_aton(args.interface)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)

    if args.ip:
        sock.sendto(GET_ID, (args.ip, PORT))

    serial = None
    while True:
        data, address = sock.recvfrom(65535)
        decoded = decode(data)
        if decoded is None:
            continue
        decoded["source_ip"] = address[0]
        if decoded["type"] == "identity":
            serial = decoded["serial"]
        elif serial is not None:
            decoded["serial"] = serial
        print(json.dumps(decoded, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
