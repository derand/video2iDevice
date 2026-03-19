# -*- coding: utf-8 -*-
"""Encoding sub-package: video, audio, and subtitle stream encoders."""

from typing import List


def _mergeFfmpegParams(current_params: List[str], user_params: List[str]) -> List[str]:
    """Merge user-supplied ffmpeg parameters into the base parameter list.

    User parameters override matching flags; ``-vf`` is ignored (video
    filters are managed separately).

    Args:
        current_params: Base ffmpeg parameter list (modified in place).
        user_params: Additional parameters to merge (consumed).

    Returns:
        The updated *current_params* list.
    """
    while len(user_params):
        idx = -1
        param = user_params[0]
        del user_params[0]
        if param[0] == '-':
            val = None
            try:
                idx = current_params.index(param)
            except Exception:
                pass
            if user_params[0][0] != '-':
                val = user_params[0]
                del user_params[0]
            if param != '-vf':
                if idx == -1:
                    current_params.insert(-1, param)
                    if val is not None:
                        current_params.insert(-1, val)
                else:
                    if val is not None:
                        current_params[idx + 1] = val
    return current_params
