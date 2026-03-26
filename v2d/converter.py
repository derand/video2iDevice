# -*- coding: utf-8 -*-
"""Main Video2iDevice converter class."""

import sys
import os
import struct
from typing import Any, List

from v2d.settings import STTNGS
from v2d.interfaces import BaseConverter
from v2d.log import LogToFile
from v2d.cli import CLIParserMixin
from v2d.runner import RunnerMixin
from v2d.tagging import TaggingMixin
from v2d.encoding.video import VideoEncoderMixin
from v2d.encoding.audio import AudioEncoderMixin
from v2d.encoding.subtitles import SubtitleEncoderMixin
from v2d.packaging import PackagingMixin
from media import MediaInformer, cMediaInfo, StreamType
from v2d_utils import (ffmpeg_path, mp4box_path, AtomicParsley_path,
                       mkvtoolnix_path, mediainfo_path)


class Video2iDevice(BaseConverter, CLIParserMixin, RunnerMixin, TaggingMixin,
                    VideoEncoderMixin, AudioEncoderMixin,
                    SubtitleEncoderMixin, PackagingMixin):
    """Main converter class: parses CLI arguments, encodes video/audio/subtitles, and packages output."""

    def __init__(self):
        super(Video2iDevice, self).__init__()
        self.mediainformer = MediaInformer(
            ffmpeg_path=ffmpeg_path,
            mkvtoolnix_path=mkvtoolnix_path,
            mediainfo_path=mediainfo_path,
            atomicParsley_path=AtomicParsley_path,
            mp4box_path=mp4box_path,
            artwork_path=STTNGS['temp_dir'],
        )
        self.log = LogToFile()

    def splitMedia(self, filename: str) -> None:
        """Trim/split *filename* using the ``ss`` setting (start[/duration]).

        Args:
            filename: Path to the media file to split in place.
        """
        if 'ss' in STTNGS:
            print('------ Split Media ------')
            fi = self.mediainformer.fileInfo(filename)
            vstreams = [s for s in fi.streams if s.type == StreamType.VIDEO]
            if len(vstreams):
                ext = filename.split('.')[-1].lower()
                tmp_fn = '.'.join(filename.split('.')[:-1]) + '_tmp.' + ext
                os.rename(filename, tmp_fn)

                stream = vstreams[0]
                w = stream.params['width']
                h = stream.params['height']
                lowQuality = h <= 320 or w <= 480
                crf = STTNGS.get('crf', 16)
                ffmpeg_params = self._videoFfmpegParamsQuality(tmp_fn, None, crf, 0, not lowQuality)
                ss_tmp = STTNGS['ss'].split('/')
                ss = ss_tmp[0]
                ffmpeg_params.extend(['-acodec', 'copy', '-ss', ss])
                if len(ss_tmp) > 1:
                    ffmpeg_params.append('-t')
                    ffmpeg_params.append(ss_tmp[1])
                ffmpeg_params.append(filename)
                self.execute_ffmpeg_command(ffmpeg_params)

    def encodeMedia(self, fi: Any) -> str:
        """Main encoding dispatch — encodes all streams and packages output.

        Args:
            fi: A media file info object whose ``.filename`` and ``.streams``
                attributes describe the source.

        Returns:
            Path to the final output file.
        """
        name = os.path.basename(fi.filename)
        files = []
        findSubs = True
        tmp = STTNGS['streams']
        strms = []
        if tmp == '' or tmp == 'all':
            for i in range(len(fi.streams)):
                strms.append(i)
        elif tmp == 'none':
            pass
        else:
            for s in tmp.split(':'):
                strms.append(s)

        # check hardsub and get unique media file names for logging
        hardsub_streams = []
        media_file_names = set()
        for i in strms:
            stream = self._streamById(i, fi.streams)
            if 'extended' in stream.params and 'hardsub' in stream.params['extended']:
                stream.params['filename'] = fi.filename
                hardsub_streams.append(stream)
            media_file_names.add(fi.filename)
        for fadd in STTNGS['fadd']:
            stream = self._streamFromFAdd(fadd, fi)
            if 'extended' in stream.params and 'hardsub' in stream.params['extended']:
                hardsub_streams.append(stream)
            media_file_names.add(stream.params['filename'])
        for x in media_file_names:
            self.log.put('----------------------------\n', False)
            self.log.put(self.mediainformer.fileInfo(x).dump(), True)
        self.log.put('----------------------------\n', False)

        currentTrack = 0
        out_fn_base = '%s/%s' % (STTNGS['temp_dir'], name)
        for i in strms:
            stream = self._streamById(i, fi.streams)
            stream.params['GlobalTrackNum'] = currentTrack
            if STTNGS['vv']:
                print(stream)

            if stream.type == StreamType.VIDEO:
                if len(hardsub_streams) > 0:
                    stream.params['hardsub_streams'] = hardsub_streams
                    hardsub_streams = []
                out_fn = '{fn}_{track}.mp4'.format(fn=out_fn_base, track=stream.trackId_short)
                files.append((0, out_fn, stream))
                self.cVideo(fi.filename, stream, files[-1][1])

            elif stream.type == StreamType.AUDIO:
                out_fn = '{fn}_{track}.aac'.format(fn=out_fn_base, track=stream.trackId_short)
                files.append((1, out_fn, stream))
                self.cAudio(fi.filename, stream, files[-1][1])

            elif stream.type == StreamType.SUBTITLE:
                out_fn = '{fn}_{track}.ttxt'.format(fn=out_fn_base, track=stream.trackId_short)
                tmpFile = self.cSubs(fi.filename, stream, fi.informer, {}, out_fn)
                if tmpFile is not None:
                    files.append((2, tmpFile, stream))
                    findSubs = False
            if STTNGS['vv']:
                print('----------------------------------------', currentTrack)
            currentTrack += 1

        # add external streams
        for add in STTNGS['fadd']:
            stream = self._streamFromFAdd(add, fi, currentTrack)
            if stream is None:
                print("Can't find stream (type: %d) in file or incorrect number" % add[0])
                sys.exit(1)

            out_fn = '%s/%s_%s' % (STTNGS['temp_dir'], os.path.basename(stream.params['filename']), stream.trackId_short)
            if stream.params['name'] is not None and stream.params['name'] != '':
                if len(stream.params['name']):
                    out_fn = '%s_%s' % (out_fn, stream.params['name'])

            print(add)
            if add[0] == 0:
                out_fn = out_fn + '.mp4'
                if len(hardsub_streams) > 0:
                    stream.params['hardsub_streams'] = hardsub_streams
                    hardsub_streams = []
                files.append((0, out_fn, stream))
                self.cVideo(stream.params['filename'], stream, files[-1][1])

            elif add[0] == 1:
                out_fn = out_fn + '.aac'
                files.append((1, out_fn, stream))
                self.cAudio(stream.params['filename'], stream, files[-1][1])

            elif add[0] == 2:
                out_fn = out_fn + '.ttxt'
                tmpFile = self.cSubs(stream.params['filename'], stream, stream.params['informer'], add[2], out_fn)
                if tmpFile is not None:
                    files.append((2, tmpFile, stream))
                    findSubs = False

            if STTNGS['vv']:
                print('----------------------------------------', currentTrack)
            currentTrack += 1

        if STTNGS['vv']:
            print()

        # write streams to output file
        fmt = STTNGS['format'].lower()
        if fmt in ['m4v', 'mp4', 'mov']:
            name = self.createMPEG(files, fi)
        elif fmt in ['mkv']:
            STTNGS['web_optimization'] = False
            name = self.createMKV(files, fi)

        self.splitMedia(name)

        self.log.put('Remove temp files...\n')
        if STTNGS['ctf']:
            for f in files:
                try:
                    os.unlink(f[1])
                except OSError as e:
                    print(('Can\'t remove file: %s' % f[1]))

        return name

    def fileProcessing(self, fi: Any) -> None:
        """Process a single input file end-to-end.

        Args:
            fi: A media file info object describing the input file.
        """
        from v2d_utils import mp4box_path
        filename = fi.filename
        if 'tagging_mode' in STTNGS:
            self.splitMedia(filename)
            self.tag_file(filename)
        else:
            filename = self.encodeMedia(fi)

        if STTNGS['web_optimization']:
            cmd = [mp4box_path, '-inter', '500', filename]
            self._exeCmd(cmd)

        self.rename(filename)

    def correct_profile(self, video: str, **kwargs: Any) -> None:
        """Fix H.264 profile flags in an MP4 container file.

        Args:
            video: Path to the MP4 file to patch.
            **kwargs: Supports ``dry_run`` (bool) and ``argv0`` (str).
        """
        if kwargs.get('dry_run', False):
            from shlex import quote as sq
            print(" ".join([sq(x) for x in (kwargs['argv0'], '--correct-profile-only', video)]))
        else:
            level_string = struct.pack('b', int('29', 16))
            with open(video, 'r+b') as fobj:
                fobj.seek(7)
                print(1, 'correcting profile:', video)
                fobj.write(level_string)
