#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""video2iDevice — entry point.  All logic lives in the v2d package."""

# writed by derand
# - Sorry for horrible code -

import sys
import os
import json
import time
import select
import shlex
import logging

from v2d import Video2iDevice, STTNGS
from v2d.settings import __version__
from v2d.log import setup_logging
from media import cMediaInfo
from v2d_utils import send_xmpp_message

__version__ = __version__
__author__ = 'Andrey Derevyagin'
__maintainer__ = 'Andrey Derevyagin'
__email__ = '2derand+2idevice@gmail.com'
__copyright__ = 'Copyright © 2010-2012, Andrey Derevyagin'


if __name__ == '__main__':
    setup_logging()

    script_path = os.path.dirname(os.path.realpath(__file__))
    # set 'FONTCONFIG_FILE' environment variable for font_config
    if os.environ.get('FONTCONFIG_FILE') is None:
        os.environ['FONTCONFIG_FILE'] = '%s/fonts.conf' % script_path

    converter = Video2iDevice()

    startTime = time.time()
    argv = sys.argv[1:]
    JSON_pipe = len(argv) == 1 and argv[0] == '-json_pipe'
    if len(sys.argv) == 1 or JSON_pipe:
        i, o, e = select.select([sys.stdin], [], [], 3)
        if i:
            if JSON_pipe:
                argv = json.loads(sys.stdin.read())
            else:
                argv = shlex.split(sys.stdin.read())
        else:
            argv = ['-h']
    yep = False
    for el in argv:
        if yep:
            STTNGS['tfile'] = el
            break
        if el == '-tfile':
            yep = True
    if len(STTNGS['tfile']) > 0:
        TAGS = converter.load_configuration_from_file(STTNGS['tfile'])
        for key, val in list(TAGS.items()):
            if key == 'TRACK_REGEX' or key == 'TRACKS_REGEX':
                if key not in STTNGS:
                    STTNGS[key] = val.split(';')
            else:
                if key not in STTNGS:
                    STTNGS[key] = val
    converter.getSettings(argv)
    if STTNGS['vv']:
        logging.getLogger().setLevel(logging.DEBUG)

    if 'out_path' in STTNGS:
        os.chdir(STTNGS['out_path'])

    if 'log_file' in STTNGS:
        converter.log.initLogByFileName(STTNGS['log_file'])
    converter.log.put('argv: %s\n' % argv.__str__(), True)

    if 'threads' not in STTNGS:
        STTNGS['threads'] = os.sysconf('SC_NPROCESSORS_CONF')
    if converter.log.isSetted():
        import platform
        converter.log.put('Version: %s\n' % STTNGS['version'], False)
        converter.log.put('Platform: %s\n' % platform.uname().__str__(), False)
        converter.log.put('Threads: %d\n\n' % STTNGS['threads'], True)

    if STTNGS['temp_dir'][-1] == '/':
        STTNGS['temp_dir'] = STTNGS['temp_dir'][:-1]
    if not os.path.exists(STTNGS['temp_dir']):
        os.mkdir(STTNGS['temp_dir'])
        logging.info('Created temp dir: %s', STTNGS['temp_dir'])

    converter.mediainformer.artwork_path = STTNGS['temp_dir']

    c = 0
    for fn in STTNGS['files']:
        logging.debug('\n------------------------ %s ------------------------', fn)
        if 'info' in STTNGS:
            fi = converter.mediainformer.fileInfo(fn)
            if STTNGS['info'] == 'json':
                print(json.dumps(fi.dump('dict')))
            elif STTNGS['info'] == 'short':
                print(fi.dump('short'))
            else:
                print(fi.dump())
        else:
            if STTNGS['sleep_between_files'] > 0 and c > 0:
                logging.info('Sleeping...')
                time.sleep(STTNGS['sleep_between_files'])
            if STTNGS['streams'] == 'none':
                fi = cMediaInfo('no need', fn)
            else:
                fi = converter.mediainformer.fileInfo(fn)
            converter.fileProcessing(fi)
        c += 1
    tm = time.time() - startTime
    time_str = '%02d:%02d:%.3f' % (tm // 60 // 60, tm % (60 * 60) // 60, int(tm % 60) + (tm - int(tm)))
    if not ('info' in STTNGS and not STTNGS['vv']):
        print('time %s' % time_str)

    converter.log.put('time %s\n' % time_str, True)

    if converter.log.isSetted():
        try:
            from constants import SERVICE_XMPP_UID, SERVICE_XMPP_PASS, XMPP_UID
            send_xmpp_message(SERVICE_XMPP_UID, SERVICE_XMPP_PASS, XMPP_UID,
                              'Convertion "%s" complite.' % '.'.join(
                                  os.path.basename(converter.log.file_name()).split('.')[:-1]))
        except Exception:
            pass

    converter.log.releaseLog()
