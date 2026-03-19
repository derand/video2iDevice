# -*- coding: utf-8 -*-
"""Video encoding mixin for Video2iDevice."""

import sys
import os
import shutil
import codecs
import fileCoding
from typing import Any, List, Optional

from v2d.settings import STTNGS, os_ffmpeg_prms
from v2d.encoding import _mergeFfmpegParams
from v2d_utils import add_separator_to_filepath
from media import isMatroshkaMedia


class VideoEncoderMixin:
    """Mixin providing video stream encoding via ffmpeg."""

    def _videoFfmpegParamsBase(self, fileName: str, _map: Optional[str]) -> List[str]:
        rv = ['-y',
              '-i', '"' + fileName + '"',
              '-map_chapters', '-1']
        if _map is not None:
            rv.append('-map')
            rv.append(_map)
        return rv

    def _videoFfmpegParamsCopy(self, fileName: str, _map: Optional[str]) -> List[str]:
        rv = self._videoFfmpegParamsBase(fileName, _map)
        rv.extend(['-vcodec', 'copy'])
        return rv

    def _videoFfmpegParamsPasses(self, fileName: str, _map: Optional[str], _pass: Optional[int]) -> List[str]:
        rv = self._videoFfmpegParamsBase(fileName, _map)
        add = []
        if _pass is not None:
            add.append('-pass')
            add.append('%s' % _pass)
        add.extend(['-vcodec', STTNGS['vcodec'],
                    '-flags', '+loop',
                    '-cmp', 'chroma',
                    '-me_method', 'full'])
        rv.extend(add)
        return rv

    def _videoFfmpegParamsCRF(self, fileName: str, _map: Optional[str], crf: Any) -> List[str]:
        rv = self._videoFfmpegParamsBase(fileName, _map)
        add = ['-vcodec', STTNGS['vcodec'],
               '-crf', '%s' % crf]
        rv.extend(add)
        return rv

    def _videoFfmpegParamsQuality(self, fileName: str, _map: Optional[str],
                                   crf: Any = 0, _pass: Any = 0,
                                   hQuality: bool = True) -> List[str]:
        if crf != 0:
            ffmpeg_params = self._videoFfmpegParamsCRF(fileName, _map, crf)
            ffmpeg_params_add = ['-refs', '%d' % STTNGS['refs'],
                                 '-threads', '%s' % STTNGS['threads']]
        else:
            ffmpeg_params = self._videoFfmpegParamsPasses(fileName, _map, _pass)
            ffmpeg_params_add = ['-b:v', '"%d k"' % STTNGS['b'],
                                 '-maxrate', '"%d k"' % STTNGS['b'],
                                 '-bufsize', '"%d k"' % int(STTNGS['b'] * 2.5),
                                 '-refs', '%d' % STTNGS['refs'],
                                 '-threads', '%s' % STTNGS['threads']]
            ffmpeg_params_add.extend(os_ffmpeg_prms)
        ffmpeg_params.extend(ffmpeg_params_add)
        ffmpeg_params_add = []
        if hQuality:
            ffmpeg_params_add = ['-partitions', '+parti4x4+parti8x8+partp4x4+partp8x8+partb8x8',
                                 '-subq', '12',
                                 '-trellis', '1',
                                 '-coder', '1',
                                 '-me_range', '32',
                                 '-level', '4.1',
                                 '-profile:v', 'high',
                                 '-bf', '12']
        else:
            ffmpeg_params_add = ['-partitions', '+parti4x4+partp8x8+partb8x8',
                                 '-subq', '6',
                                 '-trellis', '0',
                                 '-coder', '0',
                                 '-me_range', '16',
                                 '-level', '3.1',
                                 '-profile:v', 'baseline']
        ffmpeg_params.extend(ffmpeg_params_add)
        return ffmpeg_params

    def _copyFileAndChangeEncoding(self, fn_src: str, fn_dest: str) -> None:
        fCoding = fileCoding.file_encoding(fn_src)
        if fCoding.lower() == 'utf-8':
            shutil.copyfile(fn_src, fn_dest)
        else:
            BLOCKSIZE = 1024 * 10
            with codecs.open(fn_src, 'r', fCoding) as sourceFile:
                with codecs.open(fn_dest, 'w', 'utf-8') as destFile:
                    while True:
                        contents = sourceFile.read(BLOCKSIZE)
                        if not contents:
                            break
                        destFile.write(contents)

    def _prepareHardsubFile(self, hardsub_stream: Any) -> Optional[str]:
        fn = hardsub_stream.params['filename']
        _, file_ext = os.path.splitext(fn)
        file_ext = file_ext.lower()
        ass_fn = None
        if file_ext == '.ass' or file_ext == '.ssa':
            ass_fn = '%s/%s' % (STTNGS['temp_dir'], os.path.basename(fn))
            self._copyFileAndChangeEncoding(fn, ass_fn)
        elif isMatroshkaMedia(fn) and 'mkvinfo_trackNumber' in hardsub_stream.params:
            from v2d_utils import mkvtoolnix_path
            if hardsub_stream.format().upper() == 'ASS' or hardsub_stream.format().upper() == 'SSA':
                ass_fn = '%s/%s.%s' % (STTNGS['temp_dir'], os.path.basename(fn),
                                        hardsub_stream.format().lower())
                cmd = [mkvtoolnix_path + 'mkvextract', 'tracks', fn,
                       '%s:%s' % (hardsub_stream.params['mkvinfo_trackNumber'], ass_fn)]
                self._exeCmd(cmd)
            elif hardsub_stream.format().upper() == 'SRT':
                srt_fn = '%s/%s.srt' % (STTNGS['temp_dir'], os.path.basename(fn))
                cmd = [mkvtoolnix_path + 'mkvextract', 'tracks', fn,
                       '%s:%s' % (hardsub_stream.params['mkvinfo_trackNumber'], srt_fn)]
                self._exeCmd(cmd)
                ass_fn = '%s/%s.ass' % (STTNGS['temp_dir'], os.path.basename(fn))
                cmd = ['-y', '-i', srt_fn, ass_fn]
                self.execute_ffmpeg_command(cmd)
        elif file_ext == '.srt':
            ass_fn = '%s/%s.ass' % (STTNGS['temp_dir'], os.path.basename(fn))
            cmd = ['-y', '-i', fn, ass_fn]
            self.execute_ffmpeg_command(cmd)
        else:
            return None
        return ass_fn

    def cVideo(self, iFile: str, stream: Any, oFile: str) -> None:
        """Encode or copy a video stream to *oFile* using ffmpeg.

        Args:
            iFile: Path to the source media file.
            stream: A ``cStream`` object describing the video stream.
            oFile: Destination path for the encoded video track.
        """
        print(stream.params)
        w = stream.params['width']
        h = stream.params['height']
        if 'dwidth' in stream.params and 'dheight' in stream.params:
            w = stream.params['dwidth']
            h = stream.params['dheight']

        if 's' in STTNGS:
            res = STTNGS['s'].split('x')
            from v2d_utils import video_size_convert
            if res[0] == '*':
                (_h, _w) = video_size_convert(h, w, int(res[1]))
            elif res[1] == '*':
                (_w, _h) = video_size_convert(w, h, int(res[0]))
            else:
                _w = int(res[0])
                _h = int(res[1])
        else:
            (_w, _h) = (w, h)
        video_filters = []
        if _w == 480 and (_h == 368 or _h == 352): _h = 360

        print('\033[1;33m %dx%d  ==> %dx%d \033[00m' % (w, h, _w, _h))

        passes = [1, 2]
        if 'passes' in STTNGS:
            passes = []
            for el in STTNGS['passes'].split(':'):
                passes.append(int(el))

        copyFlag = STTNGS['vcopy']
        if 'extended' in stream.params:
            if 'copy' in stream.params['extended']:
                copyFlag = copyFlag or stream.params['extended']['copy']

        if copyFlag:
            passes = [1]

        crf = 0
        if 'crf' in STTNGS:
            crf = STTNGS['crf']
        else:
            if 'extended' in stream.params:
                if 'crf' in stream.params['extended']:
                    crf = stream.params['extended']['crf']
        if crf != 0:
            passes = [0]
        elif passes == [1]:
            passes = [None]

        hardsub_streams = []
        if 'hardsub_streams' in stream.params:
            hardsub_streams = stream.params['hardsub_streams']

        items2Delete = []
        for _pass in passes:
            ffmpeg_params = []
            if copyFlag:
                ffmpeg_params = self._videoFfmpegParamsCopy(iFile, stream.trackID)
                ffmpeg_params.append('-an')
            else:
                lowQuality = _h <= 320 or _w <= 480
                ffmpeg_params = self._videoFfmpegParamsQuality(iFile, stream.trackID, crf, _pass, not lowQuality)
                ffmpeg_params_add = ['-an']

                if 'vr' in STTNGS:
                    ffmpeg_params_add.extend(['-r', '%.3f' % STTNGS['vr']])

                # video filters section
                if len(hardsub_streams) == 1:
                    hardsub_stream = hardsub_streams[0]
                    ass_fn = self._prepareHardsubFile(hardsub_stream)
                    if ass_fn is not None:
                        video_filters.append({'ass': '%s' % add_separator_to_filepath(ass_fn)})
                    else:
                        print('Can\'t set stream', hardsub_stream, 'as hardsub.')
                        sys.exit(1)
                        hardsub_stream.params['extended']['hardsub'] = False
                if 'crop' in STTNGS:
                    video_filters.append({'crop': STTNGS['crop']})
                if 's' in STTNGS:
                    video_filters.append({'scale': '%d:%d' % (_w, _h)})
                if len(video_filters) > 0:
                    ffmpeg_params_add.append('-vf')
                    filter_val = ''
                    for filter_dict in video_filters:
                        filter_name = list(filter_dict.keys())[0]
                        filter_val += '%s=%s,' % (filter_name, filter_dict[filter_name])
                    ffmpeg_params_add.append(filter_val[:-1])
                ffmpeg_params.extend(ffmpeg_params_add)
            ffmpeg_params.append('"%s"' % oFile)

            if 'extended' in stream.params and 'ffmpeg_coding_params' in stream.params['extended']:
                ffmpeg_params = _mergeFfmpegParams(ffmpeg_params, stream.params['extended']['ffmpeg_coding_params'])

            if STTNGS['vc']:
                stream_prefix = None
                if 'extended' in stream.params and 'stream_prefix' in stream.params['extended']:
                    stream_prefix = stream.params['extended']['stream_prefix']
                self.execute_ffmpeg_command(ffmpeg_params, stream_prefix)

                if not copyFlag and len(passes) > 1:
                    d = 'pass%d' % _pass
                    try:
                        if not os.path.exists(d):
                            os.makedirs(d)
                        shutil.copyfile(oFile, '%s/%s' % (d, oFile))
                        items2Delete.append('%s/%s' % (d, oFile))
                        shutil.copyfile('x264_2pass.log', '%s/x264_2pass.log' % d)
                        items2Delete.append('%s/x264_2pass.log' % d)
                        items2Delete.append(d)
                    except Exception as e:
                        print(e)
        for itm in items2Delete:
            try:
                if os.path.isdir(itm):
                    os.rmdir(itm)
                else:
                    os.remove(itm)
            except Exception:
                pass
