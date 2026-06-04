# -*- coding: utf-8 -*-
"""Conversion settings dataclass and module-level STTNGS singleton."""

import sys
from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict, TYPE_CHECKING

__version__ = '0.6.0'

help = '''
Converter video for iPhone/iPod Touch/iPad
for work script you should install ffmpeg with x264 codec (http://blog.derand.net/2009/06/ffmpeg-x264.html),
MP4Box (http://gpac.sourceforge.net/doc_mp4box.php)
AtomicParsley (http://atomicparsley.sourceforge.net)
mkvtoolnix (http://www.bunkus.org/videotools/mkvtoolnix/downloads.html)
Usage
  ./2iDevice.py [options] inputFile[s]

Global options:
    -h            this help
    -th        [int]    using threads for coding
    -lang        [str]    languages of srteams separated ':' (also can set for each track like 'stream' param)
    -cn            disable converting step (files converted yet from another script run), merge streams files to .m4v file
    -streams    [str]    select streams numbers or 'none' for none (first index 0 separated ':', default 'all')
                also index can be formated [stream_type]_[stream index or stream language] where:
                    stream_type - symbol (v - video, a - audio, s - subtitle)
                    stream index - stream number, counting only for this type streams
                    stream language - search stream by language
    -tfile        [str]    set tags file
    -TRACK_REGEX    [srt]    set regular exeption for select track number from filename
    -TRACKS_REGEX    [srt]    set regular exeption for select tracks count from filename
    -out_file    [str]    save result to this file. supports tags: [SEASON], [EPISODE_ID]
    -out_path    [str]    save result to this directory
    -format        [str]    output format, can be: mp4, m4v, mkv (default: 'm4v')
    -stream        [int]    stream idx from appending files, like streams param, only one index
    -ctf            clear temp files after converting
    -v            script version
    -copy            copy selected stream from source
    -delay        [int]    sets track start delay in ms.
    -info         [str]    show media file info, value is format (can be blank), 'json' - JSON format, 'short' - short human format, default - human format
    -info1             synonim for '-info short'
    -vv            verbose mode
    -temp_dir    [str]    path to temporary directory
    -ffmpeg_coding_params    [str]    add ffmpeg params for video/audio coding (set's for selected stream), video filters disabled
    -json_pipe        set all params by JSON array [] in pipe, this should be only one param on parameters
    -web_optimization    [int]    optimization result file to streaming (0 - disabled, another - enabled(default))
    -stream_prefix    [str]    stream percentage prefix (shows when converting stream)
    -log_file         [srt]    set log file
    -ss         [str]    split media file, format: HH:MM:SS.ms/HH.MM.SS.ms
                where first - start time, second - duration (not required)
                Use "tagging_mode" for split only
    -sleep_between_files    [int]    pause between encoding files
    -test_mode        test mode, show only commands and don't execute them (default: disabled)
    -vcodec  [string]    video codec (libx264 - default)

Video options:
    -vfile        [str]    set video filename. If not set try search in current dir.
                Can be format:
                    [NAME] - origin name of file
                    [2EID] - episode id (evaluate from regext in tfile)
                    [2EC] - episode count
    -b        [int]    video bitrate (def 960)
    -crf         [int]    one pass coding, crf param
    -refs        [int]    ref frames for coding video
    -fd            fix video duration
    -s        [int]x[int]    result resolution, can looks like ('*x320', '960x*')
    -passes      [str]    video passes coding separeted ':' (use for non crf mode)
    -vr            [float]    frame rate (default 23.976)
    -crop    [int]:[int]:[int]:[int]    crop video (width:height:x:y)
    -vcopy            copy video stream from source
    -vn            disable convert video

Audio options:
    -afile        [str]    set audio filename. If not set try search in current dir.
                Can be format:
                    [NAME] - origin name of file
                    [2EID] - episode id (evaluate from regext in tfile)
                    [2EC] - episode count
    -ar        [int]    audio frequency (def 48000)
    -ab        [int]    audio bitrate (def 128k)
    -avol        [int]    change audio volume (def 256=100%), only for 'afile' params
    -acopy            copy audio stream from source
    -an            disable convert audio

Subtitle options:
    -sfile        [str]    set subtitle filename. If not set try search in current dir.
                Can be format:
                    [NAME] - origin name of file
                    [2EID] - episode id (evaluate from regext in tfile)
                    [2EC] - episode count
    -hardsub        set stream as hurdsub (for ass format only)
    -sn            disable convert subtitles
    -addTimeDiff     [int]    add time(ms) diff to subs (last sub stream)

Tagging options:
    -tagging_mode        set tags only
    -track        [int]    track
    -tracks        [int]    tracks count
    -et        [str]    set episodes titles separated ';' (for TV Shows)
    -sname        [srt]    stream title from appending files (vfile, afile, sfile)
    -add2TrackIdx    [int]    add to track (def: 0)
    -copy_warning     [str]    Add copy warning (displayed in iTunes summary page)
    -studio     [str]    Add film studio (displayed on Apple TV)
    -cast         [str]    Add Actors (displayed on Apple TV and iTunes under long description)
    -directors    [str]    Add Directors (displayed on Apple TV and iTunes under long description)
    -producers    [str]    Add Producers (displayed on Apple TV and iTunes under long description)
    -codirectors     [str]    Add Co-Directors (displayed in iTunes under long description)
    -screenwriters     [str]    Add ScreenWriters (displayed in iTunes under long description)
    -tn            disable sets tags
For tagging you can use AtomicParsley long-option params (see "AtomicParsley -h"), in param use one '-' symbol like:
    ./2iDevice.py <filename> -contentRating Unrated
for AtomicParsley --contentRating Unrated.


Author
    Writed by Andrey Derevyagin (2derand+2idevice@gmail.com)

Copyright
    Copyright © 2010-2012 Andrey Derevyagin

Bugs
    If you feel you have found a bug in "2iDevice", please email me 2derand+2idevice@gmail.com
'''

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

    # --- AtomicParsley / iTunes metadata fields ---
    artist: Optional[str] = None
    title: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    tracknum: Optional[str] = None
    disk: Optional[str] = None
    comment: Optional[str] = None
    year: Optional[str] = None
    lyrics: Optional[str] = None
    lyricsFile: Optional[str] = None
    composer: Optional[str] = None
    copyright: Optional[str] = None
    grouping: Optional[str] = None
    artwork: Optional[str] = None
    bpm: Optional[str] = None
    albumArtist: Optional[str] = None
    compilation: Optional[str] = None
    hdvideo: Optional[str] = None
    advisory: Optional[str] = None
    stik: Optional[str] = None
    description: Optional[str] = None
    longdesc: Optional[str] = None
    storedesc: Optional[str] = None
    TVNetwork: Optional[str] = None
    TVShowName: Optional[str] = None
    TVEpisode: Optional[str] = None
    TVSeasonNum: Optional[str] = None
    TVEpisodeNum: Optional[str] = None
    podcastFlag: Optional[str] = None
    category: Optional[str] = None
    keyword: Optional[str] = None
    podcastURL: Optional[str] = None
    podcastGUID: Optional[str] = None
    purchaseDate: Optional[str] = None
    encodedBy: Optional[str] = None
    apID: Optional[str] = None
    cnID: Optional[str] = None
    geID: Optional[str] = None
    xID: Optional[str] = None
    gapless: Optional[str] = None
    contentRating: Optional[str] = None
    Rating: Optional[str] = None

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
    'artist', 'title', 'album', 'genre', 'tracknum', 'disk', 'comment', 'year',
    'lyrics', 'lyricsFile', 'composer', 'copyright', 'grouping', 'artwork', 'bpm',
    'albumArtist', 'compilation', 'hdvideo', 'advisory', 'stik', 'description',
    'longdesc', 'storedesc', 'TVNetwork', 'TVShowName', 'TVEpisode', 'TVSeasonNum',
    'TVEpisodeNum', 'podcastFlag', 'category', 'keyword', 'podcastURL', 'podcastGUID',
    'purchaseDate', 'encodedBy', 'apID', 'cnID', 'geID', 'xID', 'gapless',
    'contentRating', 'Rating',
)
