import collections
import re
from typing import Any, Dict, List, Iterator  # noqa: mypy

import six
from six import text_type, binary_type  # noqa: mypy


@six.python_2_unicode_compatible
class Command(object):
    def __str__(self):
        return self._line.decode('ascii', 'replace')

    def __repr__(self):
        return '<{class_}: {str_}>'.format(
            class_=self.__class__.__name__,
            str_=str(self),
        )

    def is_valid(self):
        return True


@six.python_2_unicode_compatible
class GcodeCommand(Command):
    def __init__(self, line):
        self._line = line  # type: binary_type

    def __str__(self):
        return self._line.decode('ascii', 'replace')

    def get_main_field(self):
        # type () -> text_type
        parsed = self.get_parsed()

        return parsed[0]['field'].upper()

    def get_main_value(self):
        # type () -> float
        parsed = self.get_parsed()

        return parsed[0]['value']

    def get_name(self):
        # type () -> text_type
        parsed = self.get_parsed()

        # Do not just use 'cmd' directly since some Gcode command values
        # might have leading zeroes (M04 and M4 are equivalent)
        return u"{field}{value}".format(
            field=parsed[0]['field'],
            value=int(parsed[0]['value'])
        )

    def is_valid(self):
        # type: () -> bool
        parsed = self.get_parsed()

        # Verify that we did actually parse the whole string
        unparsed = self._line
        for cmd in reversed(parsed):
            unparsed = unparsed[:cmd['span'][0]] + unparsed[cmd['span'][1]:]
        if unparsed.strip():
            return False

        return True

    def get_parsed(self):
        # type: () -> List[Dict[str, Any]]
        fields = re.finditer(
            r'(?P<field>\w)(?P<value>[\d.-]+)', self._line
        )  # type: Iterator
        return [
            {
                'cmd': (
                    field.string[
                        field.span()[0]:field.span()[1]
                    ].decode('ascii', 'replace')
                ),
                'field': (
                    field.groupdict()[u'field']
                    .decode('ascii', 'replace').upper()
                ),
                'value': float(field.groupdict()[u'value']),
                'span': field.span()
            } for field in fields
        ]

    def get_args_dict(self):
        value = collections.OrderedDict()

        for frame in self.get_parsed()[1:]:
            value[frame['field']] = frame['value']

        return value


@six.python_2_unicode_compatible
class GrblRealtimeCommand(Command):
    STATUS = b'?'  # type: binary_type
    CYCLE_START = b'~'  # type: binary_type
    FEED_HOLD = b'!'  # type: binary_type
    SOFT_RESET = b'\x18'  # type: binary_type

    COMMANDS = {
        STATUS: u'Status',
        CYCLE_START: u'Cycle Start/Resume',
        FEED_HOLD: u'Feed Hold',
        SOFT_RESET: u'Soft Reset'
    }  # type: Dict[binary_type, text_type]

    def __init__(self, line):
        self._line = line

    @property
    def char(self):
        # type: () -> binary_type
        return self._line

    def __str__(self):
        return self.COMMANDS.get(self.char, hex(ord(self.char)))

    @classmethod
    def is_realtime_cmd(self, char):
        return char in self.COMMANDS
