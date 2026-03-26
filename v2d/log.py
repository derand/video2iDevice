# -*- coding: utf-8 -*-
"""Optional file logger that writes conversion progress to a log file."""

import logging
import sys
from typing import Optional


class CLIFormatter(logging.Formatter):
    """ANSI-colored formatter for CLI output.

    DEBUG  → grey  [debug] prefix
    INFO   → plain message
    WARNING → yellow  Warning: prefix
    ERROR  → red    Error: prefix
    """
    _FORMATS = {
        logging.DEBUG:    '\033[0;37m[debug] %(message)s\033[00m',
        logging.INFO:     '%(message)s',
        logging.WARNING:  '\033[1;33mWarning: %(message)s\033[00m',
        logging.ERROR:    '\033[1;31mError: %(message)s\033[00m',
        logging.CRITICAL: '\033[1;31mCRITICAL: %(message)s\033[00m',
    }

    def format(self, record: logging.LogRecord) -> str:
        fmt = self._FORMATS.get(record.levelno, '%(message)s')
        return logging.Formatter(fmt).format(record)


def setup_logging(verbose: bool = False) -> None:
    """Configure the root logger with :class:`CLIFormatter` on stdout.

    Args:
        verbose: If True, set level to DEBUG; otherwise INFO.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CLIFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)


class LogToFile(object):
    """Optional file logger that writes conversion progress to a log file."""

    def __init__(self):
        super(LogToFile, self).__init__()
        self.__log_file = None
        self.__file_name = None

    def __del__(self):
        self.releaseLog()

    def put(self, text: str, flush: bool = True) -> None:
        """Write *text* to the log file if one is open."""
        if self.__log_file != None:
            self.__log_file.write(text)
            if flush:
                self.flush()

    def flush(self) -> None:
        """Flush the log file buffer to disk."""
        if self.__log_file != None:
            self.__log_file.flush()

    def isSetted(self) -> bool:
        """Return True if a log file is currently open."""
        return self.__log_file != None

    def file_name(self) -> Optional[str]:
        """Return the path of the currently open log file, or None."""
        return self.__file_name

    def initLogByFileName(self, logFileName: str) -> None:
        """Open *logFileName* for writing, closing any previously open log.

        Args:
            logFileName: Path to the log file to create/overwrite.
        """
        self.releaseLog()
        self.__file_name = logFileName
        self.__log_file = open(logFileName, 'w')

    def releaseLog(self) -> None:
        """Close the log file if it is open."""
        if self.__log_file != None:
            self.__log_file.close()
            self.__log_file = None
