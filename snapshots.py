#!/usr/bin/env python
# -*- coding: utf-8 -*-


__version__ = '0.1'
__author__ = 'Andrey Derevyagin'
__maintainer__ = 'Andrey Derevyagin'
__email__ = '2derand+2idevice@gmail.com'
__copyright__ = 'Copyright © 2010-2012, Andrey Derevyagin'


import os
import sys
import argparse
from mediaInfo import cMediaInfo, MediaInformer
from v2d_utils import (ffmpeg_path, mkvtoolnix_path, mediainfo_path,
                       AtomicParsley_path, add_separator_to_filepath,
                       video_size_convert)
from subprocess import Popen, PIPE, STDOUT



shots_count = 50
snapshots_dir = './ss'

def __print_cmd(cmd):
    cmd_str = add_separator_to_filepath(cmd[0])
    for i in range(1,len(cmd)):
        if cmd[i].find(' ')==-1:
            cmd_str += ' %s'%cmd[i]
        else:
            cmd_str += ' "%s"'%cmd[i]
    #if sys.platform != 'darwin':
    #    cmd_str = cmd_str.encode('utf-8')
    print(cmd_str)


def _parse_size(value):
    """Parse size argument like '1280x720', '*x320', '960x*'."""
    parts = value.split('x')
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("Size must be in WxH format, e.g. '1280x720', '*x320'")
    return parts


if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog=os.path.basename(sys.argv[0]),
        description='Take snapshots from video files.',
        epilog='Author: %s (%s)\n%s' % (__author__, __email__, __copyright__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('files', nargs='+', metavar='file', help='media files to process')
    parser.add_argument('-c', dest='shots_count', type=int, default=shots_count,
                        metavar='INT', help='shots count per file (default: %(default)s)')
    parser.add_argument('-d', dest='snapshots_dir', default=snapshots_dir,
                        metavar='DIR', help='snapshots directory (default: %(default)s)')
    parser.add_argument('-s', dest='size', type=_parse_size, default=None,
                        metavar='WxH', help="snapshot size, e.g. '1280x720', '*x320', '960x*'")
    parser.add_argument('-f', dest='fmt', choices=['png', 'jpeg', 'jpg'], default='png',
                        metavar='FMT', help='output format: png (default) or jpeg/jpg')

    args = parser.parse_args()

    files = args.files
    shots_count = args.shots_count
    snapshots_dir = args.snapshots_dir.rstrip('/')

    _w, _h = 0, 0
    if args.size:
        w_str, h_str = args.size
        _w = 0 if w_str == '*' else int(w_str)
        _h = 0 if h_str == '*' else int(h_str)

    if args.fmt.lower() in ('jpeg', 'jpg'):
        vcodec = 'jpeg'
        out_ext = 'jpg'
    else:
        vcodec = 'png'
        out_ext = 'png'
    if not os.path.exists(snapshots_dir):
        os.mkdir(snapshots_dir)
    for fn in files:
        i = 1
        mi = MediaInformer(ffmpeg_path=ffmpeg_path, mkvtoolnix_path=mkvtoolnix_path, mediainfo_path=mediainfo_path, atomicParsley_path=AtomicParsley_path, artwork_path='/tmp')
        fi = mi.fileInfo(fn)
        if 'mediaDuration' in fi.general:
            duration = fi.general['mediaDuration']
            if duration>shots_count:
                tm = duration//(shots_count*2)
                
                cmd = [ffmpeg_path, '-ss', '',  '-i', fn, '-y']
                if vcodec=='png':
                    cmd.append('-vcodec')
                    cmd.append(vcodec)
                elif vcodec=='jpeg':
                    cmd.append('-vcodec')
                    cmd.append('mjpeg')
                cmd.extend(['-an', '-f', 'image2', '-vframes:v', '1', ''])

                if _w>0 or _h>0:
                    stream = fi.video_stream()
                    if stream==None:
                        print('Can\'t find video stream at %s'%fn)
                        sys.exit(1)
                    w = stream.params['width']
                    h = stream.params['height']
                    if 'dwidth' in stream.params and 'dheight' in stream.params:
                        w = stream.params['dwidth']
                        h = stream.params['dheight']

                    if _w==0:
                        (h, w) = video_size_convert(h, w, _h)
                    elif _h==0:
                        (w, h) = video_size_convert(w, h, _w)
                    else:
                        (w, h) = (_w, _h)
                    cmd.insert(8, '%dx%d'%(w, h))
                    cmd.insert(8, '-s')

                while tm < duration:
                    cmd[2] = '%.02f'%tm
                    cmd[-1] = '%s/%s_%03d_of_%03d(t%.02f).%s'%(snapshots_dir, os.path.splitext(os.path.basename(fn))[0], i, shots_count, tm, out_ext)
                    __print_cmd(cmd)
                
                    p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
                    while True:
                        retcode = p.poll()
                        line = p.stdout.readline().decode("utf-8")
                        if retcode is not None and len(line)==0:
                            break
                    tm += duration//shots_count
                    i += 1
