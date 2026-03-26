# -*- coding: utf-8 -*-
"""MP4/MKV container packaging mixin for Video2iDevice."""

import sys
import os
import logging
from typing import Any, List

from v2d.settings import STTNGS

logger = logging.getLogger(__name__)
from v2d.interfaces import BasePackager
from v2d_utils import mp4box_path, mkvtoolnix_path, ffmpeg_path
from mpeg4fixer import mpeg4fixer


class PackagingMixin(BasePackager):
    """Mixin providing MP4/MKV container creation via MP4Box, ffmpeg, and mkvmerge."""

    def createMPEGusingMP4Box(self, files: List, fi: Any, name: str) -> int:
        """Merge encoded stream files into an MP4 container using MP4Box.

        Args:
            files: List of ``(type, path, stream)`` tuples for each track.
            fi: Source file info object (used for tagging metadata).
            name: Output file path.

        Returns:
            MP4Box exit code (0 on success).
        """
        addCmd2 = ''
        ve = ''
        ae = ''
        se = ''
        currentTrackIdx = 0
        trackID = 0
        info = self.tagTrackInfo(os.path.basename(fi.filename))
        cmd = [mp4box_path, ]
        for f in files:
            def trackDelay(trackID):
                key = 'delay%d' % trackID
                rv = 0
                if key in STTNGS:
                    rv = STTNGS[key]
                if 'episodes' in STTNGS and 'track' in info and isinstance(info['track'], int):
                    eid = info['track'] - 1
                    if key in STTNGS['episodes'][eid]:
                        rv = STTNGS['episodes'][eid][key]
                return rv

            stream = f[2]
            delay = 0
            if 'extended' in stream.params:
                if 'delay' in stream.params['extended']:
                    delay = stream.params['extended']['delay']
            if delay == 0:
                delay = trackDelay(trackID)

            if stream is not None:
                if 'extended' in stream.params and 'lang' in stream.params['extended']:
                    (l, currentTrackIdx) = self.getLang(currentTrackIdx, stream.params['extended']['lang'])
                    l = stream.params['extended']['lang']
                else:
                    (l, currentTrackIdx) = self.getLang(currentTrackIdx, stream.language)
            else:
                (l, currentTrackIdx) = self.getLang(currentTrackIdx)
            addCmd2 = f[1]
            if l != 'und':
                addCmd2 += ':lang=%s' % l
            if delay != 0:
                addCmd2 += ':delay=%d' % delay
            if f[0] > 0:
                addCmd2 += ':group=%d' % f[0]
            if 'name' in stream.params and stream.params['name'] is not None:
                addCmd2 += ':name=%s' % stream.params['name']
            if f[0] == 0:
                addCmd2 += ve
                ve = ':disable'
            elif f[0] == 1:
                addCmd2 += ae
                ae = ':disable'
            elif f[0] == 2:
                addCmd2 += se
                se = ':disable'
            trackID += 1
            cmd.append('-add')
            cmd.append(addCmd2)

        cmd.append(name)
        cmd.append('-new')
        rv = self._exeCmd(cmd, False)
        return rv

    def createMPEGusingFfmpeg(self, files: List, fi: Any, name: str) -> int:
        """Merge encoded stream files into an MP4 container using ffmpeg.

        Used as a fallback when MP4Box fails.

        Args:
            files: List of ``(type, path, stream)`` tuples for each track.
            fi: Source file info object (unused, kept for API symmetry).
            name: Output file path.

        Returns:
            ffmpeg process exit code (0 on success).
        """
        cmd = [ffmpeg_path, '-y', ]
        for f in files:
            addCmd2 = f[1]
            cmd.append('-i')
            cmd.append(addCmd2)
        cmd.extend(['-c:v', 'copy', '-c:a', 'copy', '-bsf:a', 'aac_adtstoasc', '-strict', 'experimental'])
        cmd.append(name)
        rv = self._exeCmd(cmd, False)
        return rv

    def createMPEG(self, files: List, fi: Any) -> str:
        """Build the final MP4/M4V container, tag it, and fix flags.

        Tries MP4Box first, falls back to ffmpeg on failure.

        Args:
            files: List of ``(type, path, stream)`` tuples for each track.
            fi: Source file info object used to derive the output filename.

        Returns:
            Path to the finished output file.
        """
        name = STTNGS['temp_dir'] + '/' + '.'.join(os.path.basename(fi.filename).split('.')[:-1]) + '.' + STTNGS['format']
        ret_code = self.createMPEGusingMP4Box(files, fi, name)

        if ret_code != 0:
            rv = self.createMPEGusingFfmpeg(files, fi, name)
            if rv != 0:
                logger.error('Merge streams failed, code: %s', rv)
                sys.exit(rv)

        self.tag_file(name)

        self.log.put('Fixing flags on result mpeg file...\n')
        if not STTNGS.get('test_mode'):
            mpeg4fixer().fixFlagsAndSubs(name, STTNGS['fd'])
        return name

    def createMKV(self, files: List, fi: Any) -> str:
        """Build a Matroska (MKV) container from the encoded stream files.

        Args:
            files: List of ``(type, path, stream)`` tuples for each track.
            fi: Source file info object used to derive the output filename.

        Returns:
            Path to the finished MKV output file.
        """
        name = STTNGS['temp_dir'] + '/' + '.'.join(os.path.basename(fi.filename).split('.')[:-1]) + '.' + STTNGS['format']
        cmd = [mkvtoolnix_path + 'mkvmerge', '-o', name, ]
        for f in files:
            cmd.append(f[1])
        retcode = self._exeCmd(cmd, False)
        if retcode > 1:
            logger.error('mkvmerge failed (exit %d): %s', retcode, cmd)
            sys.exit()
        return name
