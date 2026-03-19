# -*- coding: utf-8 -*-
"""Optional file logger that writes conversion progress to a log file."""

from typing import Optional


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
