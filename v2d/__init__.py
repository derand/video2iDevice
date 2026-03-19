# -*- coding: utf-8 -*-
"""v2d package — video2iDevice core library.

Re-exports the main public API for convenience.
"""

from v2d.settings import ConversionSettings, STTNGS, atomicParsleyOptions, __version__
from v2d.log import LogToFile
from v2d.converter import Video2iDevice

__all__ = [
    'ConversionSettings',
    'STTNGS',
    'atomicParsleyOptions',
    '__version__',
    'LogToFile',
    'Video2iDevice',
]
