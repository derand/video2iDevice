#!/usr/bin/env python
# -*- coding: utf-8 -*-

# writed by derand (2derand@gmail.com)

import sys
import os
import struct


def swapBytes(bytes):
    rv = ''
    for i in bytes:
        rv = i+rv
    return rv

def getSectionInfo(f):
    pos = f.tell()
    tmp = f.read(8)
    sz = struct.unpack('I', swapBytes(tmp[:4]))[0]
    name = tmp[4:]
    return (sz, name, pos)


# ------------------------- MAIN -------------------------

if len(sys.argv)!=2:
    print '''
    Use mp4Viewer.py <videoFileName>

    where  <videoFileName> - MPEG4 video file
    '''
    sys.exit(0)

fn = sys.argv[1]
fs = os.path.getsize(fn)
f = open(fn, 'r')

pos = f.tell()
info = (0,'',0)
while (info[2]+info[0])<fs:
    info = getSectionInfo(f)
    print '%012d +%s(%d)'%(info[2], info[1], info[0])
    if info[1]=='moov':
        si = (0,'',0)
        while (si[2]+si[0])<(info[2]+info[0]):
            si = getSectionInfo(f)
            print '%012d   %s(%d)'%(si[2], si[1], si[0])
            if si[1]=='mvhd':
                mvhd_pos = si[2]
                f.seek(si[2]+24)
                movie_dur = struct.unpack('I', swapBytes(f.read(4)))[0]

            if si[1]=='trak':
                tkhd_pos = 0
                hdlr_pos = 0
                tsi = (0,'',0)
                while (tsi[2]+tsi[0])<(si[2]+si[0]):
                    tsi = getSectionInfo(f)
                    print '%012d    %s(%d)'%(tsi[2], tsi[1], tsi[0])
                    if tsi[1]=='tkhd':
                        tkhd_pos = tsi[2]
                    if tsi[1]=='mdia':
                        mtsi = (0,'',0)
                        while (mtsi[2]+mtsi[0])<(tsi[2]+tsi[0]):
                            mtsi = getSectionInfo(f)
                            print '%012d     %s(%d)'%(mtsi[2], mtsi[1], mtsi[0])
                            if mtsi[1]=='hdlr':
                                hdlr_pos = mtsi[2]
                            f.seek(mtsi[0]+mtsi[2])

                    f.seek(tsi[0]+tsi[2])

            f.seek(si[0]+si[2])

    f.seek(info[2]+info[0])
    
f.close()



