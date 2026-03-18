#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# writed by derand (2derand@gmail.com)

import os
import sys
import struct
import shutil

class mpeg4fixer:
    def __init__(self):
        pass

    def __swapBytes(self, bytes):
        return bytes[::-1]

    def __getSectionInfo(self, f):
            pos = f.tell()
            tmp = f.read(8)
            sz = struct.unpack('I', self.__swapBytes(tmp[:4]))[0]
            name = tmp[4:].rstrip(b'\x00')
            return (sz, name, pos)

    def fixFlagsAndSubs(self, fn, fixVideoDuration=False):
        SBTL = 1819566707
        with open(fn, 'rb+') as f:
            fs = os.path.getsize(fn)
            mvhd_pos = 0
            movie_dur = 0
            video_dur = 0
            pos = 0
            moov_sz = 0
            while (pos+moov_sz)<fs:
                (moov_sz, name, pos) = self.__getSectionInfo(f)
                if name==b'moov':
                    vtrack = False
                    atrack = False
                    strack = False
                    header_sz = pos+moov_sz
                    si = (0,b'',0)
                    while (si[2]+si[0])<(pos+moov_sz):
                        si = self.__getSectionInfo(f)
                        if si[1]==b'mvhd':
                            mvhd_pos = si[2]
                            f.seek(si[2]+24)
                            movie_dur = struct.unpack('I', self.__swapBytes(f.read(4)))[0]
                            print('duration: ', movie_dur)
    
                        if si[1]==b'trak':
                            tkhd_pos = 0
                            hdlr_pos = 0
                            tsi = (0,b'',0)
                            while (tsi[2]+tsi[0])<(si[2]+si[0]):
                                tsi = self.__getSectionInfo(f)
                                if tsi[1]==b'tkhd':
                                    tkhd_pos = tsi[2]
                                if tsi[1]==b'mdia':
                                    mtsi = (0,b'',0)
                                    while (mtsi[2]+mtsi[0])<(tsi[2]+tsi[0]):
                                        mtsi = self.__getSectionInfo(f)
                                        if mtsi[1]==b'hdlr':
                                            hdlr_pos = mtsi[2]
                                        f.seek(mtsi[0]+mtsi[2])
    
                                f.seek(tsi[0]+tsi[2])
                            if  tkhd_pos != 0 and hdlr_pos !=0:
                                f.seek(hdlr_pos+16)
                                ttype = f.read(4)
                                trackflags=15
                                if ttype==b'text' or ttype==b'sblt':
                                    f.seek(hdlr_pos+16)
                                    f.write(struct.pack('I', SBTL))
                                    f.seek(tkhd_pos+40)
                                    f.write(self.__swapBytes(struct.pack('I', 2)))
                                    f.seek(tkhd_pos+8)
                                    if strack: trackflags -= 1
                                    strack = True
                                    f.write(self.__swapBytes(struct.pack('I', trackflags)))
                                if ttype==b'vide':
                                    f.seek(tkhd_pos+8)
                                    if vtrack: trackflags -= 1
                                    vtrack = True
                                    f.write(self.__swapBytes(struct.pack('I', trackflags)))
                                    f.seek(tkhd_pos+28)
                                    d = struct.unpack('I', self.__swapBytes(f.read(4)))[0]
                                    if d>video_dur: video_dur=d
                                if ttype==b'soun':
                                    f.seek(tkhd_pos+8)
                                    if atrack:trackflags -= 1
                                    atrack = True
                                    f.write(self.__swapBytes(struct.pack('I', trackflags)))
                                #f.seek(tkhd_pos+28)
                                #print struct.unpack('I', self.__swapBytes(f.read(4)))
                        f.seek(si[0]+si[2])
                    # fix duration 
                    if fixVideoDuration:
                        f.seek(mvhd_pos+24)
                        print(f.write(self.__swapBytes(struct.pack('I', video_dur))))
                f.seek(pos+moov_sz)

    def __copySection(self, si, fi, fo):
        '''
            copy section (si) from fi to end fo
        '''
        buffSz = 1024*1024
        (sz, name, pos) = si
        fo.seek(0, 2)
        fi.seek(pos)
        rsz = sz
        while sz>0:
            if sz > buffSz:
                rsz = buffSz
            else:
                rsz = sz
            buff = fi.read(rsz)
            fo.write(buff)
            sz -= rsz

    def __getFileStruct(self, fn):
        rv = []
        fs = os.path.getsize(fn)
        with open(fn, 'rb') as f:
            gi = (0,b'',0)
            while (gi[2]+gi[0])<fs:
                gi = self.__getSectionInfo(f)
                add = [gi[0], gi[1], gi[2], ]
                if gi[1]==b'moov':
                    add2 = []
                    mi = (0,'',0)
                    while (mi[2]+mi[0])<(gi[2]+gi[0]):
                        mi = self.__getSectionInfo(f)
                        add3 = [mi[0], mi[1], mi[2]]
                        add2.append( add3 )
                        f.seek(mi[0]+mi[2])
                    add.append( add2 )
                rv.append( add )
                f.seek(gi[2]+gi[0])
        return rv

    def __writeFreeBlock(self, si, fo):
        (sz, name, pos) = si[:3]
        fo.seek(0, 2)
        fo.write(self.__swapBytes(struct.pack('I', sz)))
        fo.write(b'free')
        sz -= 8
        while sz>0:
            fo.write(b'x')
            sz -= 1
        '''
        buffSz = 1024*1024
        (sz, name, pos) = si
        fo.seek(0, 2)
        rsz = sz
        while sz>0:
            if sz > buffSz:
                rsz = buffSz
            else:
                rsz = sz
            buff = fi.read(rsz)
            fo.write(buff)
            sz -= rsz
        '''

    def setTrackNames(self, fn, names=[]):
        addSize = 0
        for n in names:
            if n!=None:
                addSize+=len(n)+16
        print(addSize)
        if addSize==0:
            return None
        fstruct = self.__getFileStruct(fn)
        moovIdx = -1
        mdatIdx = -1
        for i in range(len(fstruct)):
            gi = fstruct[i]
            print('%012d +%s(%d)'%(gi[2], gi[1], gi[0]))
            if gi[1]==b'moov': moovIdx = i
            if gi[1]==b'mdat': mdatIdx = i
        moveMoov = False
        if moovIdx < mdatIdx:
            gi = fstruct[moovIdx+1]
            moveMoov = (gi[1]==b'free') and ((gi[0]-8)<addSize)
        print(moveMoov)
        i = len(fstruct)-1
        while fstruct[i][1]==b'free':
            del fstruct[i]
            i-=1
        if moveMoov:
            gi = fstruct[moovIdx]
            gi[1] = b'free'
            add = (gi[0]+addSize, b'moov', gi[2], gi[3])
            fstruct.append(add)
        else:
            for i in [moovIdx-1, moovIdx+1]:
                if i>-1 and i<len(fstruct):
                    gi = fstruct[i]
                    if gi[1]==b'free':
                        if (gi[0]-8)>addSize:
                            gi[0] -= addSize
                            fstruct[moovIdx][0] += addSize
                            addSize = 0
                        else:
                            fstruct[moovIdx][0] += gi[0]-8
                            addSize -= gi[0]-8
                            gi[0] = 8
        streams = []
        for gi in fstruct:
            if gi[1]==b'free' and streams[-1][1]==b'free':
                streams[-1][0] += gi[0]
            else:
                streams.append(gi)

        of_name = '%s.tmp'%fn.split('/')[-1]
        with open(fn, 'rb') as f, open(of_name, 'wb+') as fo:
            trackCounter = 0
            for i in range(len(streams)):
                gi = streams[i]
                print('%012d +%s(%d)'%(gi[2], gi[1], gi[0]))
                if gi[1]==b'moov':
                    fo.write(self.__swapBytes(struct.pack('I', gi[0])))
                    fo.write(b'moov')
                    for mi in gi[3]:
                        self.__copySection(mi, f, fo)
                        if mi[1]==b'trak':
                            if names[trackCounter]!=None:
                                print('%012d   %s(%d)\t%s'%(mi[2], mi[1], mi[0], names[trackCounter]))
                                name_bytes = names[trackCounter].encode('utf-8') if isinstance(names[trackCounter], str) else names[trackCounter]
                                nsz = len(name_bytes) + 16
                                fo.write(self.__swapBytes(struct.pack('I', nsz)))
                                fo.write(b'udta')
                                fo.write(self.__swapBytes(struct.pack('I', nsz-8)))
                                fo.write(b'name')
                                fo.write(name_bytes)
                                fo.seek(-1*(mi[0]+nsz), 2)
                                nsz = mi[0]+nsz
                                fo.write(self.__swapBytes(struct.pack('I', nsz)))
                            else:
                                print('%012d   %s(%d)'%(mi[2], mi[1], mi[0]))
                            trackCounter += 1
                        else:
                            print('%012d   %s(%d)'%(mi[2], mi[1], mi[0]))
                elif gi[1]==b'free':
                    self.__writeFreeBlock(gi, fo)
                else:
                    self.__copySection(gi, f, fo)
        shutil.move(of_name, fn)
        return None

if __name__=='__main__':
    if len(sys.argv)==2:
        mpeg4fixer().fixFlagsAndSubs(sys.argv[1])
        #names = [None, None, 'OpenDub', 'Persona99', 'Shachiburi', 'Antravoco', 'Shift', 'Stan WarHammer & Nesitach']
        #mpeg4fixer().setTrackNames(sys.argv[1], names)
