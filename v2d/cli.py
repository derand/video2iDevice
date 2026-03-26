# -*- coding: utf-8 -*-
"""CLI argument parsing mixin for Video2iDevice."""

import sys
import json
import shlex
import codecs
import logging
import fileCoding
from typing import List, Dict, Any

from v2d.settings import STTNGS, help

logger = logging.getLogger(__name__)


class CLIParserMixin:
    """Mixin providing CLI argument parsing and settings-file loading."""

    _iTunMOVI_arrayKeys = ['cast', 'directors', 'producers', 'codirectors', 'screenwriters']

    def getSettings(self, argv: List[str]) -> None:
        """Parse command-line arguments into the global STTNGS container.

        Args:
            argv: List of raw command-line tokens (typically ``sys.argv[1:]``).
        """
        ckey = 'files'
        saveP = False
        waitParam = False
        for el in argv:
            if len(el) > 0 and el[0] == '-' and not waitParam:
                ckey = el[1:]
                if ckey == "th":
                    ckey = 'threads'
                if ckey == "et":
                    ckey = 'episodes_titles'
                saveP, waitParam = self._apply_flag(ckey)
            else:
                waitParam = False
                if saveP:
                    ckey = 'files'
                self._apply_value(ckey, el)
                saveP = True
        logger.debug('%s', STTNGS)

    def _apply_flag(self, ckey: str):
        """Process a valueless flag argument (starts with '-').

        Returns:
            Tuple of (saveP, waitParam).
        """
        saveP = False
        waitParam = False
        if ckey == 'nconvert' or ckey == 'cn':
            STTNGS['ac'] = False
            STTNGS['vc'] = False
            STTNGS['sc'] = False
            saveP = True
        if ckey == 'vn':
            STTNGS['vc'] = False
            saveP = True
        if ckey == 'an':
            STTNGS['ac'] = False
            saveP = True
        if ckey == 'sn':
            STTNGS['sc'] = False
            saveP = True
        # stream and global single params
        if ckey == 'vcopy' or ckey == 'acopy':
            tmp = STTNGS['fadd']
            if len(tmp) > 0:
                tmp[-1][-1]['copy'] = True
            else:
                STTNGS[ckey] = True
            saveP = True
        # stream single params
        if ckey == 'copy' or ckey == 'hardsub':
            tmp = STTNGS['fadd']
            if len(tmp) > 0:
                tmp[-1][-1][ckey] = True
            saveP = True
        # global single params
        if ckey in ('tn', 'fd', 'ctf', 'vv', 'tagging_mode', 'test_mode'):
            STTNGS[ckey] = True
            saveP = True
        # params whose value may start with '-'
        if ckey in ('addTimeDiff', 'add2TrackIdx', 'ffmpeg_coding_params'):
            waitParam = True
        # help / version
        if ckey == 'h' or ckey == 'json_pipe':
            print(help)
            sys.exit(0)
        if ckey == 'v':
            print("Version: %s" % STTNGS['version'])
            sys.exit(0)
        # info flags
        if ckey == 'info':
            STTNGS[ckey] = None
        if ckey == 'info1':
            STTNGS['info'] = 'short'
            saveP = True
        return saveP, waitParam

    def _apply_value(self, ckey: str, el: str) -> None:
        """Apply a parsed value to STTNGS for the current key."""
        if ckey == 'vfile' or ckey == 'afile' or ckey == 'sfile':
            tt = 2
            if ckey == 'afile': tt = 1
            if ckey == 'vfile': tt = 0
            STTNGS['fadd'].append((tt, el, {}))
        elif ckey in ('episodes_titles', 'TRACK_REGEX', 'TRACKS_REGEX'):
            STTNGS[ckey] = el.split(';')
        elif ckey == 'stream':
            tmp = STTNGS['fadd']
            if len(tmp) > 0:
                tmp[-1][-1]['stream'] = el
        elif ckey == 'sname':
            tmp = STTNGS['fadd']
            if len(tmp) > 0:
                tmp[-1][-1]['sname'] = el
        elif ckey == 'ar' and len(STTNGS['fadd']) > 0:
            STTNGS['fadd'][-1][-1]['ar'] = int(el)
        elif ckey == 'ab' and len(STTNGS['fadd']) > 0:
            STTNGS['fadd'][-1][-1]['ab'] = int(el)
        elif ckey == 'addTimeDiff' and len(STTNGS['fadd']) > 0:
            if STTNGS['fadd'][-1][0] == 2:
                STTNGS['fadd'][-1][-1]['addTimeDiff'] = int(el)
        elif ckey == 'avol':
            tmp = STTNGS['fadd']
            if len(tmp) > 0:
                tmp[-1][-1]['vol'] = el
        elif ckey == 'delay':
            tmp = STTNGS['fadd']
            if len(tmp) > 0:
                tmp[-1][-1]['delay'] = int(el)
        elif ckey == 'lang':
            tmp = STTNGS['fadd']
            if el.find(':') == -1 and len(tmp) > 0:
                tmp[-1][-1]['lang'] = el
            else:
                STTNGS[ckey] = el
        elif ckey == 'crf':
            tmp = STTNGS['fadd']
            if len(tmp) > 0:
                tmp[-1][-1]['crf'] = el
            else:
                STTNGS[ckey] = el
        elif ckey == 'ffmpeg_coding_params':
            tmp = STTNGS['fadd']
            if len(tmp) > 0:
                tmp[-1][-1][ckey] = shlex.split(el)
        elif ckey == 'web_optimization':
            STTNGS[ckey] = el != '0'
        elif ckey == 'stream_prefix':
            tmp = STTNGS['fadd']
            if len(tmp) > 0:
                tmp[-1][-1][ckey] = el
        elif ckey in self._iTunMOVI_arrayKeys:
            for tmp in el.split(','):
                STTNGS[ckey].append(tmp.strip())
        elif ckey == 'threads':
            STTNGS[ckey] = int(el)
        elif ckey == 'vcodec':
            STTNGS[ckey] = el
        else:
            # --- CLI input validation ---
            if ckey in ('ab', 'vb'):
                try:
                    val = int(el.rstrip('k'))
                    if val <= 0:
                        logger.warning('%s must be positive, got %r', ckey, el)
                except ValueError:
                    pass  # non-numeric value (e.g. 'copy') is allowed
            elif ckey == 's' and 'x' in el:
                parts = el.split('x')
                if len(parts) == 2:
                    try:
                        w_part, h_part = parts
                        if w_part != '*' and int(w_part) <= 0:
                            logger.warning('resolution width must be positive, got %r', el)
                        if h_part != '*' and int(h_part) <= 0:
                            logger.warning('resolution height must be positive, got %r', el)
                    except ValueError:
                        logger.warning('resolution must be WxH format with integers, got %r', el)
                else:
                    logger.warning('resolution must be WxH format, got %r', el)
            elif ckey in ('vr', 'r'):
                try:
                    val = float(el)
                    if val <= 0:
                        logger.warning('frame rate must be positive, got %r', el)
                except ValueError:
                    logger.warning('frame rate must be a number, got %r', el)
            # --- end validation ---
            if ckey in STTNGS:
                if isinstance(STTNGS[ckey], list):
                    STTNGS[ckey].append(el)
                elif isinstance(STTNGS[ckey], int):
                    STTNGS[ckey] = int(el)
                elif isinstance(STTNGS[ckey], float):
                    STTNGS[ckey] = float(el)
                else:
                    STTNGS[ckey] = el
            else:
                STTNGS[ckey] = el

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
        file_lines = file.read().encode('utf-8')
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
