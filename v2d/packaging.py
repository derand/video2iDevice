# -*- coding: utf-8 -*-
"""MP4/MKV container packaging mixin for Video2iDevice."""

import os
import re
import logging
import subprocess
from typing import Any, Dict, List, Optional

from v2d.settings import STTNGS
from v2d.exceptions import FfmpegError

logger = logging.getLogger(__name__)
from v2d import fonts
from v2d.interfaces import BasePackager
from v2d_utils import mp4box_path, mkvtoolnix_path, ffmpeg_path
from media import isMatroshkaMedia
from mpeg4fixer import mpeg4fixer

# "Attachment ID 2: type 'application/x-truetype-font', size …, file name 'arial.ttf'"
_ATTACHMENT_RE = re.compile(r"^Attachment ID (\d+): type '([^']*)'.*file name '(.*)'\s*$")


class PackagingMixin(BasePackager):
    """Mixin providing MP4/MKV container creation via MP4Box, ffmpeg, and mkvmerge."""

    def _tracksMeta(self, files: List, fi: Any) -> List[Dict[str, Any]]:
        """Resolve per-track metadata shared by the MP4 and MKV packagers.

        Language and delay resolution is order-dependent (``getLang`` walks the
        language list as it goes), so this runs once over all tracks and returns
        the result positionally.

        The default flag is normalised here rather than left to the muxer:
        mkvmerge preserves whatever flag a copied track carried in its source,
        so a track extracted from a file where it was not default would stay
        off even as the only subtitle in the output.

        Args:
            files: List of ``(type, path, stream)`` tuples for each track.
            fi: Source file info object (used for episode-specific delays).

        Returns:
            One dict per track, in the same order as *files*.
        """
        info = self.tagTrackInfo(os.path.basename(fi.filename))

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

        meta: List[Dict[str, Any]] = []
        currentTrackIdx = 0
        for trackID, f in enumerate(files):
            stream = f[2]
            extended = stream.params.get('extended', {}) if stream is not None else {}

            delay = extended.get('delay', 0)
            if delay == 0:
                delay = trackDelay(trackID)

            if stream is not None:
                if 'lang' in extended:
                    (l, currentTrackIdx) = self.getLang(currentTrackIdx, extended['lang'])
                    l = extended['lang']
                else:
                    (l, currentTrackIdx) = self.getLang(currentTrackIdx, stream.language)
            else:
                (l, currentTrackIdx) = self.getLang(currentTrackIdx)

            meta.append({
                'type': f[0],
                'lang': l,
                'delay': delay,
                'name': stream.params.get('name') if stream is not None else None,
                'default': bool(extended.get('default')),
                'forced': bool(extended.get('forced')),
                'sub_charset': stream.params.get('sub_charset') if stream is not None else None,
            })

        # Exactly one default per track type: the flagged track, else the first.
        for track_type in set(m['type'] for m in meta):
            same_type = [m for m in meta if m['type'] == track_type]
            flagged = [m for m in same_type if m['default']]
            chosen = flagged[0] if flagged else same_type[0]
            for m in same_type:
                m['default'] = m is chosen

        return meta

    def createMPEGusingMP4Box(self, files: List, fi: Any, name: str) -> int:
        """Merge encoded stream files into an MP4 container using MP4Box.

        Args:
            files: List of ``(type, path, stream)`` tuples for each track.
            fi: Source file info object (used for tagging metadata).
            name: Output file path.

        Returns:
            MP4Box exit code (0 on success).
        """
        cmd = [mp4box_path, ]
        for f, m in zip(files, self._tracksMeta(files, fi)):
            addCmd2 = f[1]
            if m['lang'] != 'und':
                addCmd2 += ':lang=%s' % m['lang']
            if m['delay'] != 0:
                addCmd2 += ':delay=%d' % m['delay']
            if f[0] > 0:
                addCmd2 += ':group=%d' % f[0]
            if m['name'] is not None:
                addCmd2 += ':name=%s' % m['name']
            if not m['default']:
                addCmd2 += ':disable'
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
                raise FfmpegError(['ffmpeg', 'merge', name], rv)

        self.tag_file(name, fi.filename)

        self.log.put('Fixing flags on result mpeg file...\n')
        if not STTNGS.get('test_mode'):
            mpeg4fixer().fixFlagsAndSubs(name, STTNGS['fd'])
        return name

    def _sourceAttachments(self, source: str) -> List[Dict[str, Any]]:
        """List the attachments of an MKV *source* via ``mkvmerge -i``."""
        try:
            output = subprocess.check_output([mkvtoolnix_path + 'mkvmerge', '-i', source],
                                             stderr=subprocess.STDOUT).decode('utf-8', 'replace')
        except (OSError, subprocess.CalledProcessError) as e:
            logger.warning('cannot list attachments of "%s": %s', source, e)
            return []

        attachments = []
        for line in output.splitlines():
            match = _ATTACHMENT_RE.match(line.strip())
            if match:
                attachments.append({
                    'id': match.group(1),
                    'mime': match.group(2),
                    'name': match.group(3),
                })
        return attachments

    def _attachedFontFamilies(self, sources: List[str]) -> set:
        """Return the font families already attached to the given MKV sources.

        The attachments are extracted to the temp directory and read, because a
        font's file name says nothing about the family it provides — libass
        matches on the family name stored inside the file.
        """
        families = set()
        for source in sources:
            fonts_to_read = [a for a in self._sourceAttachments(source)
                             if a['name'].lower().endswith(fonts.FONT_EXTENSIONS)]
            if not fonts_to_read:
                continue
            specs, paths = [], []
            for attachment in fonts_to_read:
                path = os.path.join(STTNGS['temp_dir'],
                                    'attached_%s_%s' % (attachment['id'], attachment['name']))
                specs.append('%s:%s' % (attachment['id'], path))
                paths.append(path)
            self._exeCmd([mkvtoolnix_path + 'mkvextract', 'attachments', source] + specs, False)
            for path in paths:
                if os.path.exists(path):
                    families |= fonts.font_families(path)
                    if STTNGS['ctf']:
                        os.unlink(path)
        return families

    def _fontAttachArgs(self, files: List, sources: List[str]) -> List[str]:
        """Build ``--attach-file`` arguments for fonts the subtitles need.

        Only fonts referenced by an ASS/SSA script and not already present in the
        source attachments are added. Families that cannot be found anywhere are
        reported and the conversion continues — the result is still playable,
        just with substituted fonts on players that can substitute.
        """
        if not STTNGS['attach_fonts']:
            return []

        scripts = [f[1] for f in files
                   if f[0] == 2 and f[1].lower().endswith(('.ass', '.ssa'))]
        if not scripts:
            return []

        required = set()
        for script in scripts:
            required |= fonts.families_from_ass(script)
        if not required:
            return []

        present = self._attachedFontFamilies(sources) if STTNGS['attachments'] else set()
        index = fonts.build_index(STTNGS['fonts_dir'])
        paths, missing = fonts.resolve(required, present, index)

        args: List[str] = []
        for path in paths:
            args.extend(['--attachment-mime-type', fonts.mime_type(path),
                         '--attach-file', path])
        if paths:
            self.log.put('Attaching %d font file(s) used by subtitles\n' % len(paths))
        if missing:
            self.log.put('WARNING: no font found for: %s\n' % ', '.join(missing))
        return args

    def createMKV(self, files: List, fi: Any, sources: Optional[List[str]] = None) -> str:
        """Build a Matroska (MKV) container from the encoded stream files.

        Track languages, names, delays and default/forced flags are all passed
        explicitly. Attachments (fonts, cover art) and chapters are carried over
        from the MKV sources by feeding each source back to mkvmerge with its
        tracks switched off.

        Args:
            files: List of ``(type, path, stream)`` tuples for each track.
            fi: Source file info object used to derive the output filename.
            sources: Media files the tracks came from, main file first. Used for
                attachments and chapters; non-Matroska entries are ignored.

        Returns:
            Path to the finished MKV output file.
        """
        name = STTNGS['temp_dir'] + '/' + '.'.join(os.path.basename(fi.filename).split('.')[:-1]) + '.' + STTNGS['format']
        cmd = [mkvtoolnix_path + 'mkvmerge', '-o', name, ]

        for f, m in zip(files, self._tracksMeta(files, fi)):
            if m['lang'] != 'und':
                cmd.extend(['--language', '0:%s' % m['lang']])
            if m['name'] is not None:
                cmd.extend(['--track-name', '0:%s' % m['name']])
            cmd.extend(['--default-track', '0:%s' % ('yes' if m['default'] else 'no')])
            if m['forced']:
                cmd.extend(['--forced-track', '0:yes'])
            if m['delay']:
                cmd.extend(['--sync', '0:%d' % m['delay']])
            if m['sub_charset']:
                cmd.extend(['--sub-charset', '0:%s' % m['sub_charset']])
            cmd.append(f[1])

        # Attachments and chapters: re-add each source with its tracks disabled.
        # Chapters come from the main file only, or they would be duplicated.
        matroska_sources = [s for s in (sources or []) if isMatroshkaMedia(s)]
        for idx, source in enumerate(matroska_sources):
            take_chapters = idx == 0
            if not STTNGS['attachments'] and not take_chapters:
                continue
            opts = ['--no-video', '--no-audio', '--no-subtitles',
                    '--no-track-tags', '--no-global-tags']
            if not take_chapters:
                opts.append('--no-chapters')
            if not STTNGS['attachments']:
                opts.append('--no-attachments')
            cmd.extend(opts + [source])

        cmd.extend(self._fontAttachArgs(files, matroska_sources))

        retcode = self._exeCmd(cmd, False)
        if retcode > 1:
            raise FfmpegError(cmd, retcode)
        return name
