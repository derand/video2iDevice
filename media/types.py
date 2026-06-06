#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Media type definitions: StreamType, cStream, cMediaInfo, cChapter."""

# writed by derand


import os
import re
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple, Union


class StreamType(IntEnum):
    """Enumeration of media stream types."""

    VIDEO = 0
    AUDIO = 1
    SUBTITLE = 2
    IMAGE = 3


class cStream(object):
    """Represents a single media stream (video, audio, subtitle, or image) within a media file."""

    def __init__(self, stream_type: StreamType, trackID: str, language: Optional[str], params: Dict[str, Any]):
        super(cStream, self).__init__()
        self.type = stream_type
        self.trackID = trackID
        self.language = language
        self.params = params

    @property
    def trackId_short(self) -> Optional[str]:
        """Return the trailing numeric portion of the track ID string."""
        r = re.search(r"(\d+)$", self.trackID)
        if r is not None:
            return r.group()
        return None

    def __str__(self):
        rv = ''
        if self.type==StreamType.VIDEO:
            rv += 'Video:'
        if self.type==StreamType.AUDIO:
            rv += 'Audio:'
        if self.type==StreamType.SUBTITLE:
            rv += 'Subtitle:'
        if self.type==StreamType.IMAGE:
            rv += 'Image:'
        rv += ' %s'%self.trackID
        rv += ', %s'%self.language
        return 'cStream %s'%rv

    def dump(self, mode: str = 'string') -> Union[str, Dict[str, Any]]:
        """Return stream info formatted as a string, short string, or dict.

        Args:
            mode: Output format — 'string' for full details, 'short' for a brief
                one-liner, or 'dict' for a dictionary representation.

        Returns:
            Formatted stream information in the requested mode.
        """
        if mode=='string':
            rv = ''
            if self.type==StreamType.VIDEO:
                rv += 'Video stream:\n'
            if self.type==StreamType.AUDIO:
                rv += 'Audio stream:\n'
            if self.type==StreamType.SUBTITLE:
                rv += 'Subtitle stream:\n'
            if self.type==StreamType.IMAGE:
                rv += 'Image:\n'
            rv += 'Track ID: %s\n'%self.trackID.rjust(32)
            val = '%s'%self.language
            rv += 'Language: %s\n'%val.rjust(32)
            for key in sorted(self.params.keys()):
                val = '%s'%self.params[key]
                rv += '%s: %s\n'%(key, val.rjust(40-len(key)))
        elif mode=='short':
            tid = self.trackId_short
            rv = 'Stream %s: '%tid
            language_str = self.params.get('Language') or self.language
            if language_str:
                language_str = '(%s)'%language_str
            else:
                language_str = ''
            if self.type==StreamType.VIDEO:
                fps = 'x'
                if self.params.get('Frame_rate'):
                    fps = self.params.get('Frame_rate').split(' ')[0]
                    if len(fps.split('.')) > 1 and fps.split('.')[1].isdigit() and int(fps.split('.')[1]) == 0:
                        fps = fps.split('.')[0]
                    fps += 'fps'
                rv += 'V%s, %s, %sx%s @%s, %s'%(language_str, self.params.get('Format') or self.params.get('codec'), self.params.get('width'), self.params.get('height'), fps, self.params.get('Bit_rate'))
            if self.type==StreamType.AUDIO:
                rv += 'A%s, %s, %s, %s'%(language_str, self.params.get('Format') or self.params.get('codec'), self.params.get('Bit_rate'), self.params.get('Sampling_rate'))
            if self.type==StreamType.SUBTITLE:
                rv += 'S%s, %s, \"%s\"'%(language_str, self.params.get('Codec_ID'), self.params.get('Title'), )
            if self.type==StreamType.IMAGE:
                rv += 'I %s, %sx%s'%(self.params.get('codec'), self.params.get('width'), self.params.get('height'))
        elif mode=='dict':
            rv = {
            'type': self.type,
            'trackID': self.trackId_short,
            'language': self.language,
            'params': self.params
            }
        return rv

    def format(self) -> str:
        """Return the codec or format string for this stream."""
        if self.type != StreamType.SUBTITLE:
            if 'Format' in self.params:
                return self.params['Format']
            if 'codec' in self.params:
                return self.params['codec']
            return ''
        # Subtitle: derive format from Codec_ID, then fall back to codec param.
        codec_id = (self.params.get('Codec_ID') or self.params.get('CodecID') or '').upper()
        if codec_id in ('S_TEXT/ASS', 'S_TEXT/SSA'):
            return codec_id.split('/')[-1].lower()   # 'ass' or 'ssa'
        if codec_id == 'S_TEXT/UTF8':
            return 'srt'
        return self.params.get('codec', '')

class cMediaInfo(object):
    """Container for all media information about a single file, including streams, tags, and chapters."""

    def __init__(self, informer: str, filename: str):
        super(cMediaInfo, self).__init__()
        self.informer = informer
        self.filename = filename
        self.streams = []
        self.tags = {}
        self.general = {}
        self.chapters = []   # not used yet

    def stream_add(self, stream: cStream) -> None:
        """Append a stream to the internal stream list."""
        self.streams.append(stream)

    def __str__(self):
        rv = 'cMediaInfo(%s, \"%s\"):'%(self.informer, self.filename)
        for stream in self.streams:
            rv = rv + ', %s'%stream
        return rv

    def dump(self, mode: str = 'string') -> Union[str, Dict[str, Any]]:
        """Return media info formatted as a string, short string, or dict.

        Args:
            mode: Output format — 'string' for full details, 'short' for a brief
                summary, or 'dict' for a dictionary representation.

        Returns:
            Formatted media information in the requested mode.
        """
        if mode=='string':
            rv = 'Informer:\t%s\nFile Name:\t%s\n\n'%(self.informer, self.filename)
            if len(list(self.general.keys())):
                rv += 'General:\n'
                for key in sorted(self.general.keys()):
                    val = '%s'%self.general[key]
                    rv += '%s: %s\n'%(key, val.rjust(40-len(key)))
                rv += '\n'

            for stream in self.streams:
                rv += '%s\n'%stream.dump(mode)

            if len(self.chapters):
                rv += 'Chapters:\n'
                for ch in self.chapters:
                    rv += '%s\n'%ch.dump(mode)

            if len(list(self.tags.keys())):
                rv += 'Tags:\n'
                for key in sorted(self.tags.keys()):
                    val = '%s'%self.tags[key]
                    rv += '%s: %s\n'%(key, val.rjust(40-len(key)))
        elif mode=='short':
            tm = self.general.get('mediaDuration', 0)
            m, s = divmod(tm, 60)
            h, m = divmod(m, 60)
            tm = '%02d:%02d:%02d'%(h, m, s)
            sz = os.stat(self.filename).st_size
            s = 'BKMGT'
            i = 0
            while i < len(s):
                if sz < 1024:
                    break
                sz = float(sz) / 1024.0
                i+=1
            suff = s[i]
            if i > 0:
                suff += 'B'
            sz = '%.2f %s'%(sz, suff)
            rv = 'File: \"%s\", %s, %s, %s'%(os.path.basename(self.filename), tm, sz, self.informer)
            for stream in self.streams:
                rv += '\n\t%s'%stream.dump(mode)
        elif mode=='dict':
            streams_arr = []
            for s in self.streams:
                streams_arr.append(s.dump(mode))
            chapters_arr = []
            for c in self.chapters:
                chapters_arr.append(c.dump(mode))
            rv = {
            'informer': self.informer,
            'filename': self.filename,
            'streams': streams_arr,
            'tags': self.tags,
            'general': self.general,
            'chapters': chapters_arr
            }
        return rv

    def video_stream(self) -> Optional[cStream]:
        """Return the first video stream, or None if no video stream exists."""
        for stream in self.streams:
            if stream.type==StreamType.VIDEO:
                return stream
        return None


class cChapter(object):
    """Represents a single chapter entry with a timestamp and title."""

    def __init__(self, time_str: str, title: str):
        super(cChapter, self).__init__()
        self.time = self.__convertTimeString(time_str)
        self.title = title

    def __convertTimeString(self, time_str: str) -> int:
        _hours = _min = _sec = _msec = 0
        tmp = re.search(r'_(\d{2})_(\d{2})_(\d{2})(\d{3})', time_str)
        if tmp:
            _hours = int(tmp.group(1))
            _min = int(tmp.group(2))
            _sec = int(tmp.group(3))
            _msec = int(tmp.group(4))
        return ((_hours*60+_min)*60+_sec)*1000+_msec

    def humanTime(self) -> Tuple[int, int, int, int]:
        """Return chapter time as a tuple of (hours, minutes, seconds, milliseconds)."""
        tm = self.time
        _hours = tm//(60*60*1000)
        tm = tm%(60*60*1000)
        _min = tm//(60*1000)
        tm = tm%(60*1000)
        _sec = tm//1000
        _msec = tm%1000
        return (_hours, _min, _sec, _msec)

    def humanTimeStr(self) -> str:
        """Return chapter time as a formatted string 'HH:MM:SS:mmm'."""
        return '%02d:%02d:%02d:%03d'%self.humanTime()

    def __str__(self):
        return 'cChapter(%s, "%s")'%(self.humanTimeStr(), self.title)

    def dump(self, mode: str = 'string') -> Union[str, List[Any]]:
        """Return chapter info as a formatted string or a [time_ms, title] list.

        Args:
            mode: Output format — 'string' for a formatted line, or 'dict' for
                a list containing the raw time in milliseconds and the title.

        Returns:
            Formatted chapter information in the requested mode.
        """
        if mode=='string':
            key = self.humanTimeStr()
            return '%s: %s'%(key, self.title.rjust(40-len(key)))
        elif mode=='dict':
            return [self.time, self.title]
