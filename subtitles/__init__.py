# -*- coding: utf-8 -*-
"""Subtitle conversion package for Video2iDevice.

Re-exports the subtitle converter so that callers can use either:
    from subConverter import subConverter   # legacy
    from subtitles import subConverter      # new-style
"""

from subConverter import subConverter

__all__ = ['subConverter']
