# -*- coding: utf-8 -*-
"""Subtitle encoding mixin for Video2iDevice."""

import sys
import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

import fileCoding
from v2d.settings import STTNGS
from v2d.interfaces import BaseSubtitleEncoder
from v2d_utils import mp4box_path, mkvtoolnix_path
from media import isMatroshkaMedia
from subtitles import subConverter

# Subtitle stream format (cStream.format()) → file extension used when the track
# is copied out of the source container instead of being converted.
_SUB_EXTENSION = {
    'ass': 'ass',   'ssa': 'ssa',
    'srt': 'srt',   'subrip': 'srt',
    'webvtt': 'vtt',
    'pgs': 'sup',   'hdmv_pgs_subtitle': 'sup',
    'vobsub': 'idx', 'dvd_subtitle': 'idx',
}

# Extensions whose content is text and therefore has a character encoding.
_TEXT_SUB_EXTENSIONS = frozenset(['ass', 'ssa', 'srt', 'vtt'])


class SubtitleEncoderMixin(BaseSubtitleEncoder):
    """Mixin providing subtitle stream extraction and conversion."""

    def _streamById(self, streamId: Any, streams: List) -> Any:
        """Find a stream by its integer index or type+index/language string."""
        separator = self.mediainformer.mapStreamSeparatedSymbol()
        if str(streamId).isdigit():
            for s in streams:
                currStreamId = s.trackID.split(separator)[-1]
                if currStreamId == str(streamId):
                    return s
        else:
            s = str(streamId).lower()
            stream_types_chars = 'vasi'
            tt = stream_types_chars.find(s[0])
            if tt > -1:
                s = s[1:]
                if len(s) > 0 and s[0] == '_': s = s[1:]
            strm = None
            if s.isdigit():
                idx = int(s)
                tmp = [a for a in streams if a.type == tt]
                if idx < len(tmp):
                    strm = tmp[idx]
            elif len(s) > 0:
                tmp = [a for a in streams if a.type == tt and a.language == s]
                if len(tmp) > 0:
                    strm = tmp[0]
            else:
                tmp = [a for a in streams if a.type == tt]
                if len(tmp) > 0:
                    strm = tmp[0]
            if strm is not None:
                return strm
        logger.error("Can't find stream #%s", streamId)
        sys.exit(1)
        return streams[streamId]

    def _streamFromFAdd(self, fadd: Any, fi: Any, currentTrack: int = 0) -> Any:
        """Build a stream object from an external file addition entry."""
        path = os.path.dirname(fi.filename)
        if path and path[-1] != '/':
            path += '/'
        nn = self.buildFN(fi.filename, fadd.path)
        if not nn[0] in '/~':
            nn = path + nn
        if not os.path.exists(nn):
            logger.error('file "%s" not exist', nn)
            sys.exit(1)
        _fi = self.mediainformer.fileInfo(nn)
        _fi.streams[0].params['GlobalTrackNum'] = currentTrack

        stream = None
        if fadd.stream is not None:
            stream = self._streamById(fadd.stream, _fi.streams)
        else:
            for i in range(len(_fi.streams)):
                tmp_stream = self._streamById(i, _fi.streams)
                if tmp_stream.type == fadd.stream_type:
                    stream = tmp_stream
                    break
        if stream is not None:
            stream.params['extended'] = fadd.as_extended_dict()
            stream.params['filename'] = _fi.filename
            stream.params['informer'] = _fi.informer
            stream.params['name'] = fadd.name
        return stream

    def _subCharset(self, iFile: str) -> Optional[str]:
        """Detect the character encoding of a text subtitle file, or None."""
        try:
            return fileCoding.file_encoding(iFile)
        except Exception as e:                      # detection is best-effort
            logger.warning('cannot detect encoding of "%s": %s', iFile, e)
            return None

    def _copySubs(self, iFile: str, stream: Any, oFile: str) -> Optional[str]:
        """Copy a subtitle track out of *iFile* keeping its original format.

        Used for MKV output, where styling must survive: ASS stays ASS instead of
        being flattened into timed text. Text tracks coming out of Matroska are
        already UTF-8 by specification, so only external files get their encoding
        sniffed for a later ``--sub-charset``.

        Args:
            iFile: Source media file or standalone subtitle file.
            stream: A ``cStream`` object describing the subtitle stream.
            oFile: Destination path proposed by the caller (``.ttxt`` suffix is
                replaced with the real subtitle extension).

        Returns:
            Path to the copied subtitle file, or None when the track cannot be
            carried over.
        """
        base = oFile[:-len('.ttxt')] if oFile.lower().endswith('.ttxt') else oFile
        ext = iFile.split('.')[-1].lower()

        # Standalone subtitle file — copy as-is.
        if ext in ('srt', 'ass', 'ssa', 'vtt', 'sup'):
            out_fn = '%s.%s' % (base, ext)
            if STTNGS['sc']:
                from shutil import copyfile
                copyfile(iFile, out_fn)
                if ext in _TEXT_SUB_EXTENSIONS:
                    stream.params['sub_charset'] = self._subCharset(iFile)
            return out_fn

        if ext in ('mp4', 'm4v', 'mov'):
            logger.error('subtitles from "%s" cannot go into mkv: timed text '
                         '(tx3g) conversion is not implemented — track skipped', iFile)
            return None

        fmt = stream.format().lower()
        sub_ext = _SUB_EXTENSION.get(fmt)
        if sub_ext is None:
            logger.error('unsupported subtitle format "%s" in "%s" — track skipped',
                         fmt, iFile)
            return None
        out_fn = '%s.%s' % (base, sub_ext)

        if isMatroshkaMedia(iFile) and 'mkvinfo_trackNumber' in stream.params:
            if STTNGS['sc']:
                cmd = [mkvtoolnix_path + 'mkvextract', 'tracks', iFile,
                       '%s:%s' % (stream.params['mkvinfo_trackNumber'], out_fn)]
                self._exeCmd(cmd)
            return out_fn

        ffmpeg_params = ['-y',
                         '-i', '"%s"' % iFile,
                         '-map', stream.trackID,
                         '-an',
                         '-vn',
                         '-scodec', 'copy',
                         out_fn]
        if STTNGS['sc']:
            stream_prefix = None
            if 'extended' in stream.params and 'stream_prefix' in stream.params['extended']:
                stream_prefix = stream.params['extended']['stream_prefix']
            self.execute_ffmpeg_command(ffmpeg_params, stream_prefix)
        return out_fn

    def cSubs(self, iFile: str, stream: Any, informer: Any, prms: Dict, oFile: str) -> Optional[str]:
        """Convert a subtitle stream to TTXT format in *oFile*.

        Args:
            iFile: Path to the source media file.
            stream: A ``cStream`` object describing the subtitle stream.
            informer: The media informer object used for stream metadata.
            prms: Extra parameters passed to the subtitle converter.
            oFile: Destination path for the converted TTXT subtitle track.

        Returns:
            The path to the output subtitle file, or None if the stream is a
            hard-subtitle that should be skipped.
        """
        if 'extended' in stream.params and 'hardsub' in stream.params['extended']:
            if stream.params['extended']['hardsub']:
                return None
            else:
                stream.params['extended']['hardsub'] = True
        if STTNGS['format'].lower() == 'mkv':
            return self._copySubs(iFile, stream, oFile)
        ext = iFile.split('.')[-1].lower()
        if ext == 'srt':
            if STTNGS['sc']:
                sConverter = subConverter(STTNGS)
                sConverter.srt2ttxt(iFile, oFile, prms)
        elif ext == 'ass' or ext == 'ssa':
            if STTNGS['sc']:
                sConverter = subConverter(STTNGS)
                sConverter.ass2ttxt(iFile, oFile, prms)
        elif ext == 'ttxt':
            from shutil import copyfile
            copyfile(iFile, oFile)
        elif ext == 'mp4' or ext == 'm4v':
            if 'copy' in stream.params.get('extended', {}):
                logger.info('subtitle from .mp4 files always copy')

            track_id = stream.params.get('mp4_track_id')
            if track_id is None:
                track_id = (int)(stream.trackID.split(self.mediainformer.mapStreamSeparatedSymbol(iFile))[1]) + 1

            fileName, fileExtension = os.path.splitext(iFile)
            tmpFile = oFile + fileExtension
            os.symlink(iFile, tmpFile)
            cmd = [mp4box_path, '-single', '%d' % track_id, tmpFile]
            self._exeCmd(cmd)
            os.unlink(tmpFile)

            fileName, fileExtension = os.path.splitext(tmpFile)
            tmpFile = fileName + '_track%d' % track_id + fileExtension
            if not os.path.exists(tmpFile):
                tmpFile = fileName + '_track%d' % track_id
            return tmpFile
        else:
            if isMatroshkaMedia(iFile) and 'mkvinfo_trackNumber' in stream.params:
                if stream.format().upper() == 'ASS' or stream.format().upper() == 'SSA':
                    assFileName = oFile + '.ass'
                    if STTNGS['sc']:
                        cmd = [mkvtoolnix_path + 'mkvextract', 'tracks', iFile,
                               '%s:%s' % (stream.params['mkvinfo_trackNumber'], assFileName)]
                        self._exeCmd(cmd)
                        sConverter = subConverter(STTNGS)
                        sConverter.ass2ttxt(assFileName, oFile, prms)
                        if STTNGS['ctf']:
                            os.unlink(assFileName)
                else:
                    strFileName = oFile + '.srt'
                    if STTNGS['sc']:
                        cmd = [mkvtoolnix_path + 'mkvextract', 'tracks', iFile,
                               '%s:%s' % (stream.params['mkvinfo_trackNumber'], strFileName)]
                        self._exeCmd(cmd)
                        sConverter = subConverter(STTNGS)
                        sConverter.srt2ttxt(strFileName, oFile)
                        if STTNGS['ctf']:
                            os.unlink(strFileName)
            else:
                tmpName = iFile.split('/')[-1] + '_%s.srt' % stream.trackID
                ffmpeg_params = ['-y',
                                 '-i', '"%s"' % iFile,
                                 '-map', stream.trackID,
                                 '-an',
                                 '-vn',
                                 '-sbsf', 'mov2textsub',
                                 '-scodec', 'copy',
                                 tmpName]
                if STTNGS['sc']:
                    stream_prefix = None
                    if 'extended' in stream.params and 'stream_prefix' in stream.params['extended']:
                        stream_prefix = stream.params['extended']['stream_prefix']
                    self.execute_ffmpeg_command(ffmpeg_params, stream_prefix)
                    sConverter = subConverter(STTNGS)
                    sConverter.ass2ttxt(tmpName, oFile)
                    if STTNGS['ctf']:
                        os.unlink(tmpName)
        return oFile
