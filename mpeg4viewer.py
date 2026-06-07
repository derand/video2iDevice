#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Command-line MPEG-4 atom structure viewer that prints the box hierarchy of an MP4 file."""


import sys
import os
import struct
from typing import BinaryIO, Tuple


def swapBytes(bytes: bytes) -> bytes:
    """Reverse a bytes object."""
    return bytes[::-1]

def getSectionInfo(f: BinaryIO) -> Tuple[int, bytes, int]:
    """Read one MPEG-4 box header and return its size, name, and file position.

    Args:
        f: Open binary file positioned at the start of a box.

    Returns:
        Tuple of (size, name, position) for the box.
    """
    pos = f.tell()
    tmp = f.read(8)
    sz = struct.unpack('I', swapBytes(tmp[:4]))[0]
    name = tmp[4:].rstrip(b'\x00')
    return (sz, name, pos)


# ------------------------- MAIN -------------------------

if len(sys.argv)!=2:
    print('''
    Use mp4Viewer.py <videoFileName>

    where  <videoFileName> - MPEG4 video file
    ''')
    sys.exit(0)

fn = sys.argv[1]
fs = os.path.getsize(fn)
with open(fn, 'rb') as f:
    
    pos = f.tell()
    info = (0,b'',0)
    while (info[2]+info[0])<fs:
        info = getSectionInfo(f)
        print('%012d +%s(%d)'%(info[2], info[1], info[0]))
        if info[1]==b'moov':
            si = (0,b'',0)
            while (si[2]+si[0])<(info[2]+info[0]):
                si = getSectionInfo(f)
                print('%012d   %s(%d)'%(si[2], si[1], si[0]))
                if si[1]==b'mvhd':
                    mvhd_pos = si[2]
                    f.seek(si[2]+24)
                    movie_dur = struct.unpack('I', swapBytes(f.read(4)))[0]
    
                if si[1]==b'trak':
                    tkhd_pos = 0
                    hdlr_pos = 0
                    tsi = (0,b'',0)
                    while (tsi[2]+tsi[0])<(si[2]+si[0]):
                        tsi = getSectionInfo(f)
                        print('%012d    %s(%d)'%(tsi[2], tsi[1], tsi[0]))
                        if tsi[1]==b'tkhd':
                            tkhd_pos = tsi[2]
                        if tsi[1]==b'mdia':
                            mtsi = (0,b'',0)
                            while (mtsi[2]+mtsi[0])<(tsi[2]+tsi[0]):
                                mtsi = getSectionInfo(f)
                                print('%012d     %s(%d)'%(mtsi[2], mtsi[1], mtsi[0]))
                                if mtsi[1]==b'hdlr':
                                    hdlr_pos = mtsi[2]
                                f.seek(mtsi[0]+mtsi[2])
    
                        f.seek(tsi[0]+tsi[2])
    
                f.seek(si[0]+si[2])
    
        f.seek(info[2]+info[0])
    
