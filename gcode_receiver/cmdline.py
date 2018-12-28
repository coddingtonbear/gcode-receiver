import argparse
import logging

from .receiver import SocketGcodeReceiver, TerminalGcodeReceiver


logger = logging.getLogger(__name__)


def getLogLevel(level):
    try:
        result = getattr(logging, level)
        if not isinstance(result, int):
            raise ValueError()
        return result
    except AttributeError:
        raise ValueError()


def main(*args, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--loglevel',
        default='INFO',
        type=getLogLevel
    )
    parser.add_argument(
        '--socket',
        type=int,
        help=(
            'Start a socket server on the specified port '
            'instead of invoking the command-line receiver.'
        )
    )
    parser.add_argument(
        '--move-delay',
        default=0.01,
        type=float,
        help='Amount of time to delay between move commands (s)'
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.loglevel
    )

    cls = TerminalGcodeReceiver
    kwargs = {
        'move_delay': args.move_delay,
    }
    if args.socket:
        cls = SocketGcodeReceiver
        kwargs['port'] = args.socket

    receiver = cls(**kwargs)
    try:
        receiver.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(e)
    finally:
        receiver.end()
