

class Response(dict):
    def __init__(self, **kwargs):
        super(Response, self).__init__(**kwargs)


class StatusResponse(Response):
    RUN = 'Run'
    IDLE = 'Idle'
