import six
from six import text_type


@six.python_2_unicode_compatible
class Response(dict):
    def __init__(self, **kwargs):
        super(Response, self).__init__(**kwargs)

    def __str__(self):
        return text_type(super(Response, self))


@six.python_2_unicode_compatible
class CommandAccepted(Response):
    def __str__(self):
        return u'ok\n'


@six.python_2_unicode_compatible
class StatusResponse(Response):
    RUN = 'Run'
    IDLE = 'Idle'

    def __str__(self):
        return u"<{state}|MPos:{x},{y},{z}|FS:{feed},{spindle}>\n".format(
            state=self['state'],
            x=self['x'],
            y=self['y'],
            z=self['z'],
            feed=self['feed_rate'],
            spindle=self['spindle_speed']
        )
