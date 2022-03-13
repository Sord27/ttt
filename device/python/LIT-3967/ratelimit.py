
"""Helper classes and function related to ratelimiting."""

import logging
import time
import threading


logger = logging.getLogger(__name__)


class Ratelimit:
    """Class for ratelimiting actions with `time.sleep()`."""

    def __init__(self, period: float):
        """Class constructor.

        Arguments:
            period: minimal allowed period (in seconds) between two requests.
        """
        self.period = period
        self.__lock = threading.Lock()
        self.__last_mono = time.monotonic() - period

    def _ratelimit(self):
        with self.__lock:
            mono = time.monotonic()
            diff = mono - self.__last_mono

            if self.period > diff:
                delay = self.period - diff

                logger.debug(f"delay action for {delay:.3f}s")
                time.sleep(delay)

                self.__last_mono = time.monotonic()
            else:
                self.__last_mono = mono

    def __enter__(self):
        """Context manager entrance point."""
        self._ratelimit()

        return self

    def __exit__(self, *_):
        """Context manager exit point."""
