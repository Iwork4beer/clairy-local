#!/usr/bin/env python3
"""Read local data from a first-generation Clairy."""

import argparse
import datetime as dt
import json
import socket
import struct
import time

GROUP = "239.0.0.1"
PORT = 6666
GET_ID = bytes.fromhex("02 09 00 ff ff 0c 00 00 02 13 03")
# Original app GET_FIRMWARE: GET_PARAMETER opcode 0x0f, parameter 0x02.
GET_FIRMWARE = bytes.fromhex("02 09 00 ff ff 0f 01 00 02 02 19 03")


def decode(data: bytes):
    """Decode packet types whose format is already confirmed."""
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


def printable(data: bytes) -> str:
    return "".join(chr(b) if 32 <= b < 127 else "." for b in data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interface",
        default="0.0.0.0",
        help="IPv4 address of the LAN interface used to join multicast",
    )
    parser.add_argument(
        "--ip",
        help="Known Clairy IPv4 address",
    )
    parser.add_argument(
        "--firmware",
        action="store_true",
        help="Send the original local firmware-version query to --ip",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print packets whose format is not yet decoded",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0,
        help="Exit after this many seconds; 0 waits forever",
    )
    args = parser.parse_args()

    if args.firmware and not args.ip:
        parser.error("--firmware requires --ip")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PORT))
    membership = socket.inet_aton(GROUP) + socket.inet_aton(args.interface)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
    sock.settimeout(1.0)

    if args.ip:
        sock.sendto(GET_ID, (args.ip, PORT))
        if args.firmware:
            sock.sendto(GET_FIRMWARE, (args.ip, PORT))
            print(
                json.dumps(
                    {
                        "type": "sent",
                        "command": "get_firmware",
                        "target": args.ip,
                        "raw_hex": GET_FIRMWARE.hex(),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    serial = None
    started = time.monotonic()
    while True:
        if args.timeout and time.monotonic() - started >= args.timeout:
            return
        try:
            data, address = sock.recvfrom(65535)
        except socket.timeout:
            continue
        if args.ip and address[0] != args.ip:
            continue

        decoded = decode(data)
        if decoded is not None:
            decoded["source_ip"] = address[0]
            if decoded["type"] == "identity":
                serial = decoded["serial"]
            elif serial is not None:
                decoded["serial"] = serial
            print(json.dumps(decoded, sort_keys=True), flush=True)
            continue

        if args.raw:
            print(
                json.dumps(
                    {
                        "type": "raw",
                        "source_ip": address[0],
                        "opcode": data[5] if len(data) > 5 else None,
                        "length": len(data),
                        "ascii": printable(data),
                        "raw_hex": data.hex(),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
