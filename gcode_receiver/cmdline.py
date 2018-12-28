import argparse
import logging

from .receiver import TerminalGcodeReceiver


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
        '--move-delay',
        default=1,
        type=float,
        help='Amount of time to delay between move commands (s)'
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.loglevel
    )

    receiver = TerminalGcodeReceiver(move_delay=args.move_delay)
    try:
        receiver.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(e)
    finally:
        receiver.end()
