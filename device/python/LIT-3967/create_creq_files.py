
from argparse import ArgumentParser
import boto3
import logging
from multiprocessing.pool import ThreadPool
import math

from ratelimit import Ratelimit


logger = logging.getLogger(__name__)


class FRPCFormatter(logging.Formatter):
    """FRPC colored logging formatter."""

    BOLD_RED = "\033[1;31m"
    BOLD_GREEN = "\033[1;32m"
    BOLD_YELLOW = "\033[1;33m"
    BOLD_CYAN = "\033[1;36m"
    BOLD_WHITE = "\033[1;37m"
    RESET = "\033[0m"
    FORMAT = "%(asctime)s: {}%(levelname)s{}: %(name)s: %(message)s"

    COLORS = {
        logging.DEBUG: BOLD_WHITE,
        logging.INFO: BOLD_GREEN,
        logging.WARNING: BOLD_YELLOW,
        logging.ERROR: BOLD_RED,
        logging.CRITICAL: BOLD_CYAN,
    }

    def format(self, record):
        """Format a logging record."""
        try:
            escapes = (self.COLORS[record.levelno], self.RESET)
        except KeyError:
            escapes = ("",) * 2

        fmt = self.FORMAT.format(*escapes)

        return logging.Formatter(fmt).format(record)


class CriticalHandler(logging.Handler):
    """Custom logging handler that calls `exit(1)` on critical log events."""

    def createLock(self):
        """Stub. No lock required for this handler."""
        self.lock = None

    def emit(self, record):
        """Crash the application on a critical event."""
        if record.levelno == logging.CRITICAL:
            sys.exit(1)


def __setup_logging():
    stream_handler = logging.StreamHandler()

    stream_handler.setFormatter(FRPCFormatter())
    stream_handler.setLevel(logging.INFO)

    critical_handler = CriticalHandler()

    logging.basicConfig(level=logging.DEBUG, handlers=[
        stream_handler,
        critical_handler
        ])


def _run_init(ratelimit):
    global _ratelimit  # pylint: disable=global-statement

    _ratelimit = ratelimit


def _run(entries):
    s3_client = boto3.client("s3")

    for entry in entries:
        with _ratelimit:
            s3_client.upload_file(*entry)
            logger.info(f"{entry} created")


def main():
    __setup_logging()

    argparser = ArgumentParser(
            description="create CREQ files for a range of mac addresses")

    argparser.add_argument("start", type=lambda x: int(x, 16))
    argparser.add_argument("end", type=lambda x: int(x, 16))
    argparser.add_argument("--threads", type=int, default=48)

    args = argparser.parse_args()
    ratelimit = Ratelimit(0.01)
    s3_client = boto3.client("s3")

    with ThreadPool(processes=args.threads, initializer=_run_init,
                    initargs=(ratelimit,)) as pool:
        put_args = [
                ("creqfile", "siq-dev-boson-devices", f"creq/{i:x}")
                for i in range(args.start, args.end + 1)
                ]

        batch_size = math.ceil(len(put_args) / args.threads)
        partitions = [
                put_args[i: i + batch_size]
                for i in range(0, len(put_args), batch_size)
                ]

        for _ in pool.imap_unordered(_run, partitions):
            pass


if __name__ == "__main__":
    main()
