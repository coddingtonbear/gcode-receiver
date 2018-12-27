import argparse
import logging
from multiprocessing import Process

from .receiver import GcodeReceiver


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
        default='DEBUG',
        type=getLogLevel
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.loglevel
    )

    receiver = GcodeReceiver()
    receiver.run_forever()
