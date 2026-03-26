# -*- coding: utf-8 -*-
"""Audio encoding mixin for Video2iDevice."""

import os
from typing import Any, List

from v2d.settings import STTNGS
from v2d.interfaces import BaseAudioEncoder
from v2d.encoding import _mergeFfmpegParams


class AudioEncoderMixin(BaseAudioEncoder):
    """Mixin providing audio stream encoding via ffmpeg."""

    def _audioFfmpegParamsBase(self, fileName: str, _map: str) -> List[str]:
        return ['-y',
                '-i', '"' + fileName + '"',
                '-map', _map,
                '-vn']

    def _audioFfmpegParamsCopy(self, fileName: str, _map: str) -> List[str]:
        rv = self._audioFfmpegParamsBase(fileName, _map)
        rv.extend(['-acodec', 'copy'])
        return rv

    def _audioFfmpegParamsAac(self, fileName: str, _map: str, _ab: int, _ar: int) -> List[str]:
        rv = self._audioFfmpegParamsBase(fileName, _map)
        rv.extend(['-acodec', 'aac',
                   '-ac', '2',
                   '-ab', '%dk' % _ab,
                   '-ar', '%d' % _ar])
        return rv

    def _audioFfmpegParamsTmpAc3(self, filename: str, _map: str, _ab: int, _ar: int, _threads: int) -> List[str]:
        rv = self._audioFfmpegParamsBase(filename, _map)
        rv.extend(['-acodec', 'ac3',
                   '-ac', '6',
                   '-ab', '%dk' % _ab,
                   '-ar', '%d' % _ar,
                   '-threads', '%d' % _threads])
        return rv

    def cAudio(self, iFile: str, stream: Any, oFile: str) -> None:
        """Encode or copy an audio stream to *oFile* using ffmpeg.

        Args:
            iFile: Path to the source media file.
            stream: A ``cStream`` object describing the audio stream.
            oFile: Destination path for the encoded audio track.
        """
        ar = STTNGS['ar']
        ab = STTNGS['ab']
        copyFlag = False
        vol = 256
        if 'extended' in stream.params:
            if 'ar' in stream.params['extended']:
                ar = stream.params['extended']['ar']
            if 'ab' in stream.params['extended']:
                ab = stream.params['extended']['ab']
            if 'vol' in stream.params['extended']:
                vol = int(stream.params['extended']['vol'])
            if 'copy' in stream.params['extended']:
                copyFlag = stream.params['extended']['copy']
        else:
            copyFlag = STTNGS['acopy']
        if 'frequency' in stream.params and ar > stream.params['frequency']:
            ar = stream.params['frequency']
        if 'bitrate' in stream.params and ab > stream.params['bitrate']:
            ab = stream.params['bitrate']
        if 'vol' in stream.params:
            vol = int(stream.params['vol'])

        ffmpeg_params = []
        ffmpeg_params_add = []
        if copyFlag or (stream.format().lower() == 'aac' and
                        'channels' in stream.params and stream.params['channels'] == '2' and
                        'bitrate' in stream.params and stream.params['bitrate'] == ab and
                        'frequency' in stream.params and stream.params['frequency'] == ar):
            ffmpeg_params = self._audioFfmpegParamsCopy(iFile, stream.trackID)
        else:
            ffmpeg_params = self._audioFfmpegParamsAac(iFile, stream.trackID, ab, ar)
            ffmpeg_params_add = ['-threads', '%d' % STTNGS['threads']]
            if vol != 256:
                ffmpeg_params_add.extend(['-vol', '%d' % vol])
            ffmpeg_params.extend(ffmpeg_params_add)
            ffmpeg_params_add = ffmpeg_params
            ffmpeg_params.extend(['-strict', 'experimental'])
        ffmpeg_params.append('"%s"' % oFile)

        if 'extended' in stream.params and 'ffmpeg_coding_params' in stream.params['extended']:
            ffmpeg_params = _mergeFfmpegParams(ffmpeg_params, stream.params['extended']['ffmpeg_coding_params'])

        if STTNGS['ac']:
            stream_prefix = None
            if 'extended' in stream.params and 'stream_prefix' in stream.params['extended']:
                stream_prefix = stream.params['extended']['stream_prefix']
            if self.execute_ffmpeg_command(ffmpeg_params, stream_prefix)[0] != 0:
                tmp_fn = '%s/tmp.ac3' % STTNGS['temp_dir']
                ffmpeg_params = self._audioFfmpegParamsTmpAc3(iFile, stream.trackID, 448, ar, STTNGS['threads'])
                ffmpeg_params.append('"%s"' % tmp_fn)
                self.execute_ffmpeg_command(ffmpeg_params, stream_prefix)
                ffmpeg_params = ffmpeg_params_add
                try:
                    idx = ffmpeg_params.index('-i')
                except Exception as e:
                    raise e
                ffmpeg_params[idx + 1] = '"%s"' % tmp_fn
                try:
                    idx = ffmpeg_params.index('-map')
                except Exception as e:
                    raise e
                del ffmpeg_params[idx:idx + 2]
                ffmpeg_params.append('"%s"' % oFile)

                if 'extended' in stream.params and 'ffmpeg_coding_params' in stream.params['extended']:
                    ffmpeg_params = _mergeFfmpegParams(ffmpeg_params, stream.params['extended']['ffmpeg_coding_params'])

                self.execute_ffmpeg_command(ffmpeg_params, stream_prefix)
                os.remove(tmp_fn)
