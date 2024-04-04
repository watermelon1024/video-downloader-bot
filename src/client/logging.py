"""
Provide logging functionality for the bot.
"""

import inspect
import logging
import sys
from datetime import timedelta

from loguru._logger import Core, Logger  # pylint: disable=wrong-import-position


class Logging:
    """
    The Loguru library provides loggers to deal with logging in Python.
    This class provides a pre-instanced (and configured) logger for the bot.
    * Stop using print() and use this instead smh.

    :ivar __logger: The logger instance.
    :vartype __logger: loguru._logger.Logger
    """

    def __init__(self, retention: timedelta, debug_mode: bool = False, format: str = None) -> None:
        """
        Initialize the logger instance.
        """
        level = "DEBUG" if debug_mode else "INFO"
        self._logger = Logger(
            core=Core(),
            exception=None,
            depth=0,
            record=False,
            lazy=False,
            colors=False,
            raw=False,
            capture=True,
            patchers=[],
            extra={},
        )
        self._logger.disable("py-cord")
        self._logger.add(sys.stderr, level=level, diagnose=False, enqueue=True, format=format)
        self._logger.add(
            "./logs/{time:YYYY-MM-DD_HH-mm-ss_SSS}.log",
            rotation="00:00",
            retention=retention,
            encoding="utf-8",
            compression="gz",
            diagnose=False,
            level=level,
            enqueue=True,
            format=format,
        )
        self._logger.debug(
            f"Logger initialized. Debug mode {'enabled' if debug_mode else 'disabled'}."
        )

    def get_logger(self) -> Logger:
        """
        The logger instance.

        :return: The logger instance.
        :rtype: loguru._logger.Logger
        """
        return self._logger


class InterceptHandler(logging.Handler):
    def __init__(self, logger: Logger) -> None:
        super().__init__()
        self.logger = logger

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = self.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        self.logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
