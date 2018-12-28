import logging
import fcntl
from multiprocessing import Process
from multiprocessing.queues import Empty, Queue
import os
import sys
import tty
from typing import Any  # noqa: mypy

from six import text_type, binary_type  # noqa: mypy

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
        try:
            data = sys.stdin.read(1)
        except IOError:
            data = None

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
        # type: (Any) -> None
        if isinstance(output, StatusResponse):
            state = u"<{state}|MPos:{x},{y},{z}|FS:{feed},{spindle}>".format(
                state=output['state'],
                x=output['x'],
                y=output['y'],
                z=output['z'],
                feed=output['feed_rate'],
                spindle=output['spindle_speed']
            )
            sys.stdout.write((state + '\n').encode('ascii'))
        elif isinstance(output, text_type):
            sys.stdout.write((output + '\n').encode('ascii'))
        else:
            logger.error(
                "Unhandled response type: %s",
                output,
            )

    def start(self):
        # Convert terminal to "uncooked" mode
        tty.setcbreak(sys.stdin.fileno())
        # Make input pipe non-blocking
        stdin_flags = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
        fcntl.fcntl(
            sys.stdin.fileno(), fcntl.F_SETFL, stdin_flags | os.O_NONBLOCK
        )

        self.send_output(u"FakeGrbl 0.1")

        while True:
            command = self.get_command()
            if command:
                if command.is_valid():
                    logger.debug('Sending command to worker: %s', command)
                    if isinstance(command, GcodeCommand):
                        self.send_output(u"ok")
                    self._outqueue.put(command)
                else:
                    logger.error('Invalid command: %s', command)
                    self.send_output(u"error")

            while not self._inqueue.empty():
                try:
                    result = self._inqueue.get_nowait()
                    logger.debug('Received worker response: %s', result)
                    self.send_output(result)
                except Empty:
                    pass

    def end(self):
        self.proc.terminate()
