"""Refuse any socket that is not the local machine.

connect raises. connect_ex returns an error code and does not connect.
A name can still be resolved by the OS before either call; that lookup is
not covered here.
"""

from __future__ import annotations

import errno
import socket

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}
# connect_ex reports failure as a number. Access denied, without opening anything.
BLOCKED_ERRNO = getattr(errno, "WSAEACCES", errno.EACCES)


class EgressGuard:
    def __init__(self) -> None:
        self.seen: list[str] = []
        self.blocked: list[str] = []
        self._orig_connect = None
        self._orig_connect_ex = None

    def _host(self, address) -> str:
        return address[0] if isinstance(address, tuple) else str(address)

    def _allowed(self, host: str) -> bool:
        if host in LOCAL_HOSTS:
            self.seen.append(host)
            return True
        self.blocked.append(host)
        return False

    def __enter__(self) -> "EgressGuard":
        self._orig_connect = socket.socket.connect
        self._orig_connect_ex = socket.socket.connect_ex

        def connect(sock, address):
            host = self._host(address)
            if self._allowed(host):
                return self._orig_connect(sock, address)
            raise OSError(f"egress blocked: {host}")

        def connect_ex(sock, address):
            host = self._host(address)
            if self._allowed(host):
                return self._orig_connect_ex(sock, address)
            return BLOCKED_ERRNO

        socket.socket.connect = connect
        socket.socket.connect_ex = connect_ex
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._orig_connect is not None:
            socket.socket.connect = self._orig_connect
            self._orig_connect = None
        if self._orig_connect_ex is not None:
            socket.socket.connect_ex = self._orig_connect_ex
            self._orig_connect_ex = None
