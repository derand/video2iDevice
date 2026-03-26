# -*- coding: utf-8 -*-
"""Utility helpers for Video2iDevice.

Re-exports from the top-level utility modules so that callers can use either:
    from v2d_utils import ffmpeg_path     # legacy
    from utils import ffmpeg_path         # new-style
"""

from v2d_utils import (
    ffmpeg_path,
    mp4box_path,
    mkvtoolnix_path,
    AtomicParsley_path,
    mediainfo_path,
    add_separator_to_filepath,
    video_size_convert,
    send_xmpp_message,
)
from fileCoding import file_encoding
from mpeg4fixer import mpeg4fixer

__all__ = [
    'ffmpeg_path',
    'mp4box_path',
    'mkvtoolnix_path',
    'AtomicParsley_path',
    'mediainfo_path',
    'add_separator_to_filepath',
    'video_size_convert',
    'send_xmpp_message',
    'file_encoding',
    'mpeg4fixer',
]
