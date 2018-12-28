import logging
import fcntl
from multiprocessing import Process
from multiprocessing.queues import Empty, Queue
import os
import socket
import sys
import time
import tty
from typing import Any, Optional  # noqa: mypy

from six import text_type, binary_type  # noqa: mypy

from .commands import Command  # noqa: mypy
from .commands import GcodeCommand, GrblRealtimeCommand
from .worker import Worker


logger = logging.getLogger(__name__)


class GcodeReceiver(object):
    def __init__(self, move_delay=None, **kwargs):
        super(GcodeReceiver, self).__init__(**kwargs)

        self._inqueue = Queue()
        self._outqueue = Queue()

        self._current_line = b""

        self.proc = Process(
            target=Worker.create,
            kwargs={
                'inqueue': self._outqueue,
                'outqueue': self._inqueue,
                'move_delay': move_delay,
            }
        )
        self.proc.start()

    def get_command(self):
        # type: () -> Optional[Command]
        data = self.get_input()

        if GrblRealtimeCommand.is_realtime_cmd(data):
            return GrblRealtimeCommand(data)

        if data is not None:
            self._current_line += data

        if b'\n' in self._current_line:
            if not self._current_line.strip():
                self._current_line = b""
                return None

            result = GcodeCommand(
                self._current_line.strip()
            )
            self._current_line = b""
            return result

        return None

    def get_input(self):
        # type: () -> Optional[binary_type]
        raise NotImplementedError()

    def send_output(self, output):
        # type: (text_type) -> None
        raise NotImplementedError()

    def start(self):
        self.send_output(u"FakeGrbl 0.1\n\n")

        while True:
            command = self.get_command()
            if command:
                if command.is_valid():
                    logger.debug('Sending command to worker: %s', command)
                    self._outqueue.put(command)
                else:
                    logger.error('Invalid command: %s', command)
                    self.send_output(u"error\n")

            while not self._inqueue.empty():
                try:
                    result = self._inqueue.get_nowait()
                    logger.debug(
                        'Received worker response: %s',
                        str(result).strip()
                    )
                    self.send_output(text_type(result))
                except Empty:
                    pass

    def end(self):
        self.proc.terminate()


class TerminalGcodeReceiver(GcodeReceiver):
    def get_input(self):
        # type: () -> Optional[binary_type]
        try:
            return sys.stdin.read(1)
        except IOError:
            return None

    def send_output(self, output):
        # type: (text_type) -> None
        sys.stdout.write(output.encode('ascii'))

    def start(self):
        # Convert terminal to "uncooked" mode
        tty.setcbreak(sys.stdin.fileno())
        # Make input pipe non-blocking
        stdin_flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(
            sys.stdin.fileno(), fcntl.F_SETFL, stdin_flags | os.O_NONBLOCK
        )
        super(TerminalGcodeReceiver, self).start()


class SocketGcodeReceiver(GcodeReceiver):
    def __init__(self, port=8300, **kwargs):
        super(SocketGcodeReceiver, self).__init__(**kwargs)
        self._port = port

        # Will be set when connection is accepted in .start
        self._connection = None
        self._address = None

    def get_input(self):
        # type: () -> Optional[binary_type]
        try:
            return self._connection.recv(1)
        except socket.error:
            return None

    def send_output(self, output):
        # type: (text_type) -> None
        self._connection.sendall(output.encode('ascii'))

    def start(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(('localhost', self._port))
        self._socket.listen(10)  # Max connections
        self._socket.setblocking(0)

        logger.info('Listening on port %s', self._port)

        while True:
            try:
                self._connection, self._address = self._socket.accept()
                logger.info(
                    'Accepted connection from %s', self._address
                )
            except socket.error:
                time.sleep(0.1)
                continue

            super(SocketGcodeReceiver, self).start()
