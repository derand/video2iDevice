# -*- coding: utf-8 -*-
"""Custom exceptions for Video2iDevice."""

from typing import List


class FfmpegError(Exception):
    """Raised when an ffmpeg (or mkvmerge) command exits with a non-zero code."""

    def __init__(self, cmd: List[str], retcode: int) -> None:
        self.cmd = cmd
        self.retcode = retcode
        super().__init__('Command failed (exit %d): %s' % (retcode, cmd))
