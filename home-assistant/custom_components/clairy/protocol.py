from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import socket
import struct
from typing import Callable

from .const import GET_ID, MULTICAST_GROUP, PORT

STALE_AFTER_SECONDS = 180


@dataclass
class ClairyReading:
    source_ip: str
    temperature: float
    humidity: float
    air_quality: float
    fan_on: bool
    fan_speed: int
    received: datetime


class ClairyProtocol(asyncio.DatagramProtocol):
    def __init__(self, manager: "ClairyManager") -> None:
        self.manager = manager

    def datagram_received(self, data: bytes, addr) -> None:
        self.manager.process(data, addr[0])


class ClairyManager:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.transport = None
        self.reading: ClairyReading | None = None
        self.serial: str | None = None
        self.callbacks: set[Callable[[], None]] = set()
        self._probed: set[str] = set()
        self._stale = True
        self._stale_handle: asyncio.TimerHandle | None = None

    @property
    def available(self) -> bool:
        return self.reading is not None and not self._stale

    async def start(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", PORT))
        membership = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0")
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        sock.setblocking(False)
        self.transport, _ = await self.loop.create_datagram_endpoint(
            lambda: ClairyProtocol(self), sock=sock
        )

    async def stop(self) -> None:
        if self._stale_handle is not None:
            self._stale_handle.cancel()
            self._stale_handle = None
        if self.transport is not None:
            self.transport.close()
            self.transport = None

    def subscribe(self, callback: Callable[[], None]) -> Callable[[], None]:
        self.callbacks.add(callback)
        return lambda: self.callbacks.discard(callback)

    def _notify(self) -> None:
        for callback in tuple(self.callbacks):
            callback()

    def _schedule_stale(self) -> None:
        if self._stale_handle is not None:
            self._stale_handle.cancel()
        self._stale_handle = self.loop.call_later(
            STALE_AFTER_SECONDS, self._mark_stale
        )

    def _mark_stale(self) -> None:
        self._stale_handle = None
        if not self._stale:
            self._stale = True
            self._notify()

    def process(self, data: bytes, source_ip: str) -> None:
        if len(data) >= 15 and data[5] == 13:
            value = struct.unpack_from("<I", data, 8)[0]
            self.serial = f"{value:09d}"
            self._notify()
            return

        if len(data) < 19 or data[5] != 1:
            return

        temperature, humidity, quality, fan, speed = struct.unpack_from(
            "<HHHBB", data, 8
        )
        self.reading = ClairyReading(
            source_ip=source_ip,
            temperature=temperature / 10.0,
            humidity=humidity / 10.0,
            air_quality=quality / 10.0,
            fan_on=bool(fan),
            fan_speed=speed,
            received=datetime.now(timezone.utc),
        )
        self._stale = False
        self._schedule_stale()
        if source_ip not in self._probed and self.transport is not None:
            self._probed.add(source_ip)
            self.transport.sendto(GET_ID, (source_ip, PORT))
        self._notify()
