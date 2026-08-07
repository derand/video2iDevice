# -*- coding: utf-8 -*-
"""Conversion settings dataclass and module-level STTNGS singleton."""

import sys
from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict

__version__ = '0.7.0'

if sys.platform == 'darwin':
    os_ffmpeg_prms = []
else:
    os_ffmpeg_prms = []


@dataclass
class StreamSpec:
    """Describes one external stream added via -vfile / -afile / -sfile."""

    stream_type: int    # 0=video, 1=audio, 2=subtitle
    path: str           # file path template (may contain [NAME], [2EID] etc.)

    stream: Optional[str] = None                    # stream selector within the file
    name: Optional[str] = None                      # display title (sname)
    lang: Optional[str] = None
    ar: Optional[int] = None                        # audio sample rate override
    ab: Optional[int] = None                        # audio bitrate override (kbps)
    vol: Optional[str] = None                       # audio volume (256 = 100%)
    delay: Optional[int] = None                     # track start delay (ms)
    crf: Optional[Any] = None
    add_time_diff: Optional[int] = None             # subtitle time offset (ms)
    ffmpeg_coding_params: Optional[List[str]] = None
    stream_prefix: Optional[str] = None
    copy: bool = False
    hardsub: bool = False
    default: bool = False                           # mark track as default (mkv/mp4)
    forced: bool = False                            # mark track as forced (mkv only)

    def as_extended_dict(self) -> Dict:
        """Return dict compatible with stream.params['extended']."""
        d: Dict[str, Any] = {}
        if self.stream is not None:               d['stream'] = self.stream
        if self.name is not None:                 d['sname'] = self.name
        if self.lang is not None:                 d['lang'] = self.lang
        if self.ar is not None:                   d['ar'] = self.ar
        if self.ab is not None:                   d['ab'] = self.ab
        if self.vol is not None:                  d['vol'] = self.vol
        if self.delay is not None:                d['delay'] = self.delay
        if self.crf is not None:                  d['crf'] = self.crf
        if self.add_time_diff is not None:        d['addTimeDiff'] = self.add_time_diff
        if self.ffmpeg_coding_params is not None: d['ffmpeg_coding_params'] = self.ffmpeg_coding_params
        if self.stream_prefix is not None:        d['stream_prefix'] = self.stream_prefix
        if self.copy:                             d['copy'] = True
        if self.hardsub:                          d['hardsub'] = True
        if self.default:                          d['default'] = True
        if self.forced:                           d['forced'] = True
        return d


@dataclass
class ConversionSettings:
    """Typed settings container for a single video conversion job."""

    # --- Core conversion flags ---
    version: str = ''
    files: List[str] = field(default_factory=list)
    ac: bool = True          # convert audio streams
    vc: bool = True          # convert video streams
    sc: bool = True          # convert subtitle streams
    lang: str = ''           # languages separated by ':'
    ar: int = 48000          # audio sample rate (Hz)
    ab: int = 128            # audio bitrate (kbps)
    b: int = 960             # video bitrate (kbps)
    refs: int = 2            # reference frames
    tn: bool = False         # disable tagging
    streams: str = ''        # stream selection
    tfile: str = ''          # tags settings file path
    fd: bool = False         # fix video duration
    fadd: List['StreamSpec'] = field(default_factory=list)  # per-stream additions
    format: str = 'm4v'      # output format (m4v, mp4, mkv)
    add2TrackIdx: int = 0
    vcodec: str = 'libx264'
    vcopy: bool = False      # copy video stream without re-encoding
    acopy: bool = False      # copy audio stream without re-encoding
    vr: float = 23.976       # video frame rate (fps)
    ctf: bool = False        # clear temp files after converting
    vv: bool = False         # verbose/debug mode
    attachments: bool = True    # copy attachments (fonts, cover) from mkv sources
    attach_fonts: bool = True   # attach fonts referenced by subtitles but missing
    fonts_dir: List[str] = field(default_factory=lambda: ['~/.fonts', '~/.fonts/subs'])
    web_optimization: bool = True
    temp_dir: str = '.'
    encodingTool: str = '2iDevice'
    cast: List[str] = field(default_factory=list)
    directors: List[str] = field(default_factory=list)
    producers: List[str] = field(default_factory=list)
    codirectors: List[str] = field(default_factory=list)
    screenwriters: List[str] = field(default_factory=list)
    sleep_between_files: int = 0

    # --- Optional runtime fields (None = not set) ---
    threads: Optional[int] = None
    info: Optional[str] = None
    track: Optional[int] = None
    tracks: Optional[int] = None
    TRACK_REGEX: Optional[List[str]] = None
    TRACKS_REGEX: Optional[List[str]] = None
    episodes_titles: Optional[List[str]] = None
    episodes: Optional[Any] = None
    out_file: Optional[str] = None
    out_path: Optional[str] = None
    log_file: Optional[str] = None
    copy_warning: Optional[str] = None
    studio: Optional[str] = None
    test_mode: Optional[bool] = None
    tagging_mode: Optional[bool] = None
    ss: Optional[str] = None
    crf: Optional[Any] = None
    s: Optional[str] = None
    passes: Optional[str] = None
    crop: Optional[str] = None
    ffmpeg_coding_params: Optional[List[str]] = None
    subStyleColors: Optional[Any] = None
    subReplace: Optional[Dict] = None
    ASSremoveItems: Optional[Any] = None

    # --- AtomicParsley / iTunes metadata ---
    title: Optional[str] = None
    comment: Optional[str] = None
    artwork: Optional[str] = None
    stik: Optional[str] = None
    description: Optional[str] = None
    longdesc: Optional[str] = None
    year: Optional[str] = None
    TVShowName: Optional[str] = None
    TVNetwork: Optional[str] = None
    TVEpisode: Optional[str] = None
    TVSeasonNum: Optional[str] = None
    TVEpisodeNum: Optional[str] = None
    Rating: Optional[str] = None
    contentRating: Optional[str] = None

    # --- Dict-compatible interface (backward compatibility) ---

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        try:
            return getattr(self, key) is not None
        except AttributeError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        try:
            val = getattr(self, key)
            return val if val is not None else default
        except AttributeError:
            return default


STTNGS = ConversionSettings(version=__version__)

atomicParsleyOptions = (
    'title', 'comment', 'artwork', 'stik', 'description', 'longdesc',
    'TVShowName', 'TVNetwork', 'TVEpisode', 'TVSeasonNum', 'TVEpisodeNum',
    'year', 'Rating', 'contentRating',
)
