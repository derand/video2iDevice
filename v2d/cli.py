# -*- coding: utf-8 -*-
"""CLI argument parsing mixin for Video2iDevice."""

import sys
import json
import shlex
import codecs
import logging
import argparse
import fileCoding
from typing import List, Dict, Any

from v2d.settings import STTNGS, StreamSpec

logger = logging.getLogger(__name__)


# ── Custom argparse actions ────────────────────────────────────────────────────

class _AddStreamAction(argparse.Action):
    """Appends a new StreamSpec to namespace.fadd for -vfile / -afile / -sfile."""
    _type_map = {'-vfile': 0, '-afile': 1, '-sfile': 2}

    def __call__(self, parser, namespace, values, option_string=None):
        namespace.fadd.append(StreamSpec(
            stream_type=self._type_map[option_string],
            path=values,
        ))


class _StreamFlagAction(argparse.Action):
    """Sets a boolean flag on the last StreamSpec (-hardsub, -copy)."""

    def __call__(self, parser, namespace, values, option_string=None):
        if namespace.fadd:
            setattr(namespace.fadd[-1], self.dest, True)


class _DualFlagAction(argparse.Action):
    """-vcopy / -acopy: per-stream copy flag if fadd is non-empty, else global."""

    def __call__(self, parser, namespace, values, option_string=None):
        if namespace.fadd:
            namespace.fadd[-1].copy = True
        else:
            flag = 'vcopy' if option_string == '-vcopy' else 'acopy'
            setattr(namespace, flag, True)


class _StreamValueAction(argparse.Action):
    """Applies a value to the last StreamSpec; silently ignored when fadd is empty."""

    def __call__(self, parser, namespace, values, option_string=None):
        if namespace.fadd:
            setattr(namespace.fadd[-1], self.dest, values)


class _DualValueAction(argparse.Action):
    """Per-stream if fadd is non-empty, else sets the value globally on namespace."""

    def __call__(self, parser, namespace, values, option_string=None):
        if namespace.fadd:
            setattr(namespace.fadd[-1], self.dest, values)
        else:
            setattr(namespace, self.dest, values)


class _LangAction(argparse.Action):
    """-lang: per-stream when fadd is non-empty and value has no ':', else global."""

    def __call__(self, parser, namespace, values, option_string=None):
        if namespace.fadd and ':' not in values:
            namespace.fadd[-1].lang = values
        else:
            namespace.lang = values


class _AddTimeDiffAction(argparse.Action):
    """-addTimeDiff INT: applies to the last StreamSpec only if it is a subtitle."""

    def __call__(self, parser, namespace, values, option_string=None):
        if namespace.fadd and namespace.fadd[-1].stream_type == 2:
            namespace.fadd[-1].add_time_diff = values


class _FfmpegCodingParamsAction(argparse.Action):
    """-ffmpeg_coding_params STR: shlex-splits and applies to the last StreamSpec."""

    def __call__(self, parser, namespace, values, option_string=None):
        if namespace.fadd:
            namespace.fadd[-1].ffmpeg_coding_params = shlex.split(values)


class _DisableAllEncodingAction(argparse.Action):
    """-cn / -nconvert: set vc/ac/sc to False (merge-only mode)."""

    def __call__(self, parser, namespace, values, option_string=None):
        namespace.vc = False
        namespace.ac = False
        namespace.sc = False


class _ArrayAppendAction(argparse.Action):
    """Splits a comma-separated string and appends each item to a list attribute."""

    def __call__(self, parser, namespace, values, option_string=None):
        current = getattr(namespace, self.dest) or []
        current.extend(item.strip() for item in values.split(','))
        setattr(namespace, self.dest, current)


# ── Mixin ──────────────────────────────────────────────────────────────────────

class CLIParserMixin:
    """Mixin providing CLI argument parsing and settings-file loading."""

    _iTunMOVI_arrayKeys = ['cast', 'directors', 'producers', 'codirectors', 'screenwriters']

    def _build_parser(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(
            prog='2iDevice.py',
            description='Convert video for iPhone/iPod Touch/iPad',
            add_help=False,
            allow_abbrev=False,
        )

        # ── Positional ─────────────────────────────────────────────────────
        p.add_argument('files', nargs='*', metavar='FILE')

        # ── Global encoding ────────────────────────────────────────────────
        p.add_argument('-b',       dest='b',      type=int,   metavar='INT',   help='video bitrate kbps (def 960)')
        p.add_argument('-s',       dest='s',                  metavar='WxH',   help='output resolution e.g. *x720')
        p.add_argument('-crf',     dest='crf',    action=_DualValueAction,     metavar='INT',   help='one-pass CRF quality value')
        p.add_argument('-refs',    dest='refs',   type=int,   metavar='INT',   help='H.264 reference frames')
        p.add_argument('-passes',  dest='passes',             metavar='STR',   help="coding passes e.g. '1:2'")
        p.add_argument('-vr',      dest='vr',     type=float, metavar='FLOAT', help='frame rate (def 23.976)')
        p.add_argument('-ar',      dest='ar',     type=int,   action=_DualValueAction, metavar='INT', help='audio sample rate Hz (def 48000)')
        p.add_argument('-ab',      dest='ab',     type=int,   action=_DualValueAction, metavar='INT', help='audio bitrate kbps (def 128)')
        p.add_argument('-format',  dest='format', choices=['mp4', 'm4v', 'mkv'],        help='output format (def m4v)')
        p.add_argument('-streams', dest='streams',            metavar='STR',   help="stream selection e.g. 'v:a' or '0:1'")
        p.add_argument('-vcodec',  dest='vcodec',             metavar='STR',   help='video codec (def libx264)')
        p.add_argument('-lang',    dest='lang',   action=_LangAction,          metavar='STR',   help="language codes e.g. 'eng:rus'")
        p.add_argument('-crop',    dest='crop',               metavar='W:H:X:Y', help='crop video')

        # ── Global flags ───────────────────────────────────────────────────
        p.add_argument('-vcopy',         dest='vcopy',        action=_DualFlagAction,          nargs=0, help='copy video without re-encoding')
        p.add_argument('-acopy',         dest='acopy',        action=_DualFlagAction,          nargs=0, help='copy audio without re-encoding')
        p.add_argument('-vn',            dest='vc',           action='store_false', default=None, help='disable video stream')
        p.add_argument('-an',            dest='ac',           action='store_false', default=None, help='disable audio stream')
        p.add_argument('-sn',            dest='sc',           action='store_false', default=None, help='disable subtitle stream')
        p.add_argument('-cn', '-nconvert', dest='_cn',        action=_DisableAllEncodingAction, nargs=0, help='disable all encoding (merge only)')
        p.add_argument('-fd',            dest='fd',           action='store_const', const=True,  help='fix video duration')
        p.add_argument('-ctf',           dest='ctf',          action='store_const', const=True,  help='clear temp files after encoding')
        p.add_argument('-vv',            dest='vv',           action='store_const', const=True,  help='verbose / debug mode')
        p.add_argument('-tn',            dest='tn',           action='store_const', const=True,  help='disable tagging')
        p.add_argument('-tagging_mode',  dest='tagging_mode', action='store_const', const=True,  help='tag only, skip encoding')
        p.add_argument('-test_mode',     dest='test_mode',    action='store_const', const=True,  help='dry run — print commands without executing')
        p.add_argument('-web_optimization', dest='web_optimization', type=lambda x: x != '0', metavar='0|1', help='fast-start optimization (def 1)')
        p.add_argument('-ss',            dest='ss',           metavar='TIME',  help='split: start[/duration] HH:MM:SS.ms')
        p.add_argument('-sleep_between_files', dest='sleep_between_files', type=int, metavar='INT', help='pause between files (seconds)')
        p.add_argument('-threads', '-th', dest='threads',     type=int, metavar='INT', help='thread count')
        p.add_argument('-temp_dir',      dest='temp_dir',     metavar='DIR')
        p.add_argument('-out_file',      dest='out_file',     metavar='FILE',  help='output filename (supports [SEASON], [EPISODE_ID])')
        p.add_argument('-out_path',      dest='out_path',     metavar='DIR',   help='output directory')
        p.add_argument('-tfile',         dest='tfile',        metavar='FILE',  help='tags/settings file')
        p.add_argument('-log_file',      dest='log_file',     metavar='FILE')
        p.add_argument('-TRACK_REGEX',   dest='TRACK_REGEX',  type=lambda s: s.split(';'), metavar='RE')
        p.add_argument('-TRACKS_REGEX',  dest='TRACKS_REGEX', type=lambda s: s.split(';'), metavar='RE')
        p.add_argument('-add2TrackIdx',  dest='add2TrackIdx', type=int, metavar='INT')
        p.add_argument('-track',         dest='track',        type=int, metavar='INT')
        p.add_argument('-tracks',        dest='tracks',       type=int, metavar='INT')

        # ── Info mode ──────────────────────────────────────────────────────
        p.add_argument('-info',  dest='info', nargs='?', const='default',      metavar='FMT',
                       help='show media file info (json | short | default)')
        p.add_argument('-info1', dest='info', action='store_const', const='short',
                       help='shorthand for -info short')

        # ── Help / version ─────────────────────────────────────────────────
        p.add_argument('-h', action='help', default=argparse.SUPPRESS,
                       help='show this help message and exit')
        p.add_argument('-v', action='version', version='Version: %s' % STTNGS['version'])

        # ── External stream file additions ─────────────────────────────────
        p.add_argument('-vfile', dest='_vfile', action=_AddStreamAction, metavar='FILE', help='add external video track')
        p.add_argument('-afile', dest='_afile', action=_AddStreamAction, metavar='FILE', help='add external audio track')
        p.add_argument('-sfile', dest='_sfile', action=_AddStreamAction, metavar='FILE', help='add external subtitle file')

        # ── Per-stream flag modifiers ──────────────────────────────────────
        p.add_argument('-hardsub', dest='hardsub', action=_StreamFlagAction, nargs=0, help='render as hard subtitles (ASS only)')
        p.add_argument('-copy',    dest='copy',    action=_StreamFlagAction, nargs=0, help='copy stream without re-encoding')

        # ── Per-stream value modifiers ─────────────────────────────────────
        p.add_argument('-stream',               dest='stream',              action=_StreamValueAction,        metavar='STR',  help='stream selector within the external file')
        p.add_argument('-sname',                dest='name',                action=_StreamValueAction,        metavar='STR',  help='stream display name')
        p.add_argument('-avol',                 dest='vol',                 action=_StreamValueAction,        metavar='INT',  help='audio volume (256=100%%)')
        p.add_argument('-delay',                dest='delay',               action=_StreamValueAction, type=int, metavar='MS', help='track start delay (ms)')
        p.add_argument('-addTimeDiff',          dest='add_time_diff',       action=_AddTimeDiffAction, type=int, metavar='MS', help='subtitle time offset (ms)')
        p.add_argument('-ffmpeg_coding_params', dest='ffmpeg_coding_params',action=_FfmpegCodingParamsAction,  metavar='STR',  help='extra ffmpeg params for this stream')
        p.add_argument('-stream_prefix',        dest='stream_prefix',       action=_StreamValueAction,        metavar='STR',  help='progress line prefix for this stream')

        # ── iTunMOVI arrays ────────────────────────────────────────────────
        p.add_argument('-cast',          dest='cast',          action=_ArrayAppendAction, metavar='STR')
        p.add_argument('-directors',     dest='directors',     action=_ArrayAppendAction, metavar='STR')
        p.add_argument('-producers',     dest='producers',     action=_ArrayAppendAction, metavar='STR')
        p.add_argument('-codirectors',   dest='codirectors',   action=_ArrayAppendAction, metavar='STR')
        p.add_argument('-screenwriters', dest='screenwriters', action=_ArrayAppendAction, metavar='STR')

        # ── Episode titles ─────────────────────────────────────────────────
        p.add_argument('-et', '-episodes_titles', dest='episodes_titles',
                       type=lambda s: s.split(';'), metavar='STR')

        # ── AtomicParsley metadata ─────────────────────────────────────────
        ap = p.add_argument_group('metadata (passed to AtomicParsley)')
        ap.add_argument('-title',         dest='title')
        ap.add_argument('-comment',       dest='comment')
        ap.add_argument('-artwork',       dest='artwork',       metavar='FILE')
        ap.add_argument('-stik',          dest='stik',          metavar='TYPE',  help='"TV Show", Movie, …')
        ap.add_argument('-description',   dest='description')
        ap.add_argument('-longdesc',      dest='longdesc')
        ap.add_argument('-year',          dest='year',          metavar='YYYY')
        ap.add_argument('-TVShowName',    dest='TVShowName')
        ap.add_argument('-TVNetwork',     dest='TVNetwork')
        ap.add_argument('-TVEpisode',     dest='TVEpisode')
        ap.add_argument('-TVSeasonNum',   dest='TVSeasonNum',   metavar='INT')
        ap.add_argument('-TVEpisodeNum',  dest='TVEpisodeNum',  metavar='INT')
        ap.add_argument('-Rating',        dest='Rating')
        ap.add_argument('-contentRating', dest='contentRating')

        return p

    def getSettings(self, argv: List[str]) -> None:
        """Parse command-line arguments into the global STTNGS container.

        Args:
            argv: List of raw command-line tokens (typically ``sys.argv[1:]``).
        """
        # Pre-initialise the namespace so ordered stream actions can append to fadd.
        ns = argparse.Namespace(fadd=[], **{k: None for k in self._iTunMOVI_arrayKeys})
        parser = self._build_parser()
        try:
            parser.parse_args(argv, namespace=ns)
        except SystemExit as e:
            sys.exit(e.code)

        # -info FILE edge-case: argparse consumed a filename as the optional format value.
        if ns.info not in (None, 'default', 'json', 'short'):
            ns.files.append(ns.info)
            ns.info = 'default'

        # Positional files (extend so tfile-loaded files are preserved)
        STTNGS['files'].extend(ns.files)

        # Stream additions (always replace — fadd starts empty each run)
        STTNGS['fadd'] = ns.fadd

        # iTunMOVI array fields (extend existing list from tfile if any)
        for key in self._iTunMOVI_arrayKeys:
            val = getattr(ns, key)
            if val:
                STTNGS[key].extend(val)

        # All other non-None, non-private values → STTNGS
        _skip = frozenset(['files', 'fadd'] + self._iTunMOVI_arrayKeys)
        for key, val in vars(ns).items():
            if key.startswith('_') or key in _skip or val is None:
                continue
            STTNGS[key] = val

        logger.debug('%s', STTNGS)

    def load_configuration_from_file(self, filename: str) -> Dict[str, Any]:
        """Load settings from a configuration file into a dictionary.

        Args:
            filename: Path to the configuration/tags file to read.

        Returns:
            A dict mapping setting names to their parsed values.
        """
        file = 0
        try:
            encoding = fileCoding.file_encoding(filename)
            file = codecs.open(filename, mode='r', encoding=encoding)
        except (OSError, UnicodeDecodeError):
            logger.error('error open file %s', filename)
            sys.exit(1)
        inside_key = False
        save_key = ''
        _tmp = ''
        rv = {}
        arrSymb = None
        file_lines = file.read()
        for line in file_lines.split('\n'):
            if len(line) < 1 or line[0] == '#':
                continue
            if inside_key:
                _tmp += line.strip()
                if _tmp[-1] == arrSymb:
                    if inside_key:
                        logger.debug('%s', _tmp)
                        rv[save_key] = json.loads(_tmp)
                        inside_key = False
            else:
                tmp = line.split('=', 1)
                if len(tmp) != 2:
                    continue
                (key, val) = (tmp[0].strip(), tmp[1].strip())
                if val[0] == '[' or val[0] == '{':
                    if val[0] == '[': arrSymb = ']'
                    if val[0] == '{': arrSymb = '}'
                    if val[-1] == arrSymb:
                        rv[key] = json.loads(val)
                    else:
                        save_key = key
                        _tmp = val
                        inside_key = True
                else:
                    if key in self._iTunMOVI_arrayKeys:
                        for tmp in val.split(','):
                            STTNGS[key].append(tmp.strip())
                    rv[key] = val
        return rv
