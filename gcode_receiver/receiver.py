import logging
import fcntl
from multiprocessing import Process
from multiprocessing.queues import Empty, Queue
import os
import sys
import tty
from typing import Any, Optional  # noqa: mypy

from six import text_type, binary_type  # noqa: mypy

from .commands import Command  # noqa: mypy
from .commands import GcodeCommand, GrblRealtimeCommand
from .responses import StatusResponse
from .worker import Worker


logger = logging.getLogger(__name__)


class GcodeReceiver(object):
    def __init__(self, move_delay=None, **kwargs):
        super(GcodeReceiver, self).__init__(**kwargs)

        self._inqueue = Queue()
        self._outqueue = Queue()

        self._current_line = ""

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

        if '\n' in self._current_line:
            if not self._current_line.strip():
                self._current_line = ""
                return None

            result = GcodeCommand(self._current_line.strip())
            self._current_line = ""
            return result

        return None

    def send_output(self, output):
        # type: (text_type) -> None
        raise NotImplementedError()

    def get_input(self):
        # type: () -> Optional[text_type]
        raise NotImplementedError()

    def start(self):
        self.send_output(u"FakeGrbl 0.1\n\n")

        while True:
            command = self.get_command()
            if command:
                if command.is_valid():
                    logger.debug('Sending command to worker: %s', command)
                    if isinstance(command, GcodeCommand):
                        self.send_output(u"ok\n")
                    self._outqueue.put(command)
                else:
                    logger.error('Invalid command: %s', command)
                    self.send_output(u"error\n")

            while not self._inqueue.empty():
                try:
                    result = self._inqueue.get_nowait()
                    logger.debug('Received worker response: %s', result)
                    self.send_output(text_type(result))
                except Empty:
                    pass

    def end(self):
        self.proc.terminate()


class TerminalGcodeReceiver(GcodeReceiver):
    def __init__(self, **kwargs):
        super(TerminalGcodeReceiver, self).__init__(**kwargs)
        # Convert terminal to "uncooked" mode
        tty.setcbreak(sys.stdin.fileno())
        # Make input pipe non-blocking
        stdin_flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(
            sys.stdin.fileno(), fcntl.F_SETFL, stdin_flags | os.O_NONBLOCK
        )

    def send_output(self, output):
        sys.stdout.write(output.encode('ascii'))

    def get_input(self):
        try:
            data = sys.stdin.read(1)
        except IOError:
            data = None

        return data
