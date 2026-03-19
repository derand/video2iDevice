# -*- coding: utf-8 -*-
"""Subtitle encoding mixin for Video2iDevice."""

import sys
import os
from typing import Any, Dict, List, Optional

from v2d.settings import STTNGS
from v2d_utils import mp4box_path, mkvtoolnix_path
from media import isMatroshkaMedia
from subConverter import subConverter


class SubtitleEncoderMixin:
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
        print('Can\'t found stream #%s' % streamId)
        sys.exit(1)
        return streams[streamId]

    def _streamFromFAdd(self, fadd: Any, fi: Any, currentTrack: int = 0) -> Any:
        """Build a stream object from an external file addition entry."""
        path = os.path.dirname(fi.filename)
        if path[-1] != '/':
            path += '/'
        nn = self.buildFN(fi.filename, fadd[1])
        if not nn[0] in '/~':
            nn = path + nn
        if not os.path.exists(nn):
            print('file "%s" not exist' % nn)
            sys.exit(1)
        _fi = self.mediainformer.fileInfo(nn)
        _fi.streams[0].params['GlobalTrackNum'] = currentTrack
        name = None
        if 'sname' in fadd[-1]:
            name = fadd[-1]['sname']

        stream = None
        if 'stream' in fadd[2]:
            stream = self._streamById(fadd[2]['stream'], _fi.streams)
        else:
            for i in range(len(_fi.streams)):
                tmp_stream = self._streamById(i, _fi.streams)
                if tmp_stream.type == fadd[0]:
                    stream = tmp_stream
                    break
        if stream is not None:
            stream.params['extended'] = fadd[-1]
            stream.params['filename'] = _fi.filename
            stream.params['informer'] = _fi.informer
            stream.params['name'] = name
        return stream

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
                print('subtitle from .mp4 files always copy')

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
