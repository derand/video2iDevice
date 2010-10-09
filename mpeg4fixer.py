#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import struct

class mpeg4fixer:
	def __init__(self):
		pass

	def __swapBytes(self, bytes):
			rv = ''
			for i in bytes:
				rv = i+rv
			return rv

	def __getSectionInfo(self, f):
			pos = f.tell()
			tmp = f.read(8)
			sz = struct.unpack('I', self.__swapBytes(tmp[:4]))[0]
			name = tmp[4:]
			#print '%08d %s %8d'%(pos, name, sz)
			return (sz, name, pos)

	def fixFlagsAndSubs(self, fn, fixVideoDuration=False):
		SBTL = 1819566707
		f = open(fn, 'r+')
		fs = os.path.getsize(fn)
		mvhd_pos = 0
		movie_dur = 0
		video_dur = 0
		pos = 0
		moov_sz = 0
		while (pos+moov_sz)<fs:
			(moov_sz, name, pos) = self.__getSectionInfo(f)
			if name=='moov':
				vtrack = False
				atrack = False
				strack = False
				header_sz = pos+moov_sz
				si = (0,'',0)
				while (si[2]+si[0])<(pos+moov_sz):
					si = self.__getSectionInfo(f)
					if si[1]=='mvhd':
						mvhd_pos = si[2]
						f.seek(si[2]+24)
						movie_dur = struct.unpack('I', self.__swapBytes(f.read(4)))[0]
						print 'duration: ', movie_dur

					if si[1]=='trak':
						tkhd_pos = 0
						hdlr_pos = 0
						tsi = (0,'',0)
						while (tsi[2]+tsi[0])<(si[2]+si[0]):
							tsi = self.__getSectionInfo(f)
							if tsi[1]=='tkhd':
								tkhd_pos = tsi[2]
							if tsi[1]=='mdia':
								mtsi = (0,'',0)
								while (mtsi[2]+mtsi[0])<(tsi[2]+tsi[0]):
									mtsi = self.__getSectionInfo(f)
									if mtsi[1]=='hdlr':
										hdlr_pos = mtsi[2]
									f.seek(mtsi[0]+mtsi[2])

							f.seek(tsi[0]+tsi[2])
						if  tkhd_pos != 0 and hdlr_pos !=0:
							f.seek(hdlr_pos+16)
							ttype = f.read(4)
							trackflags=15
							if ttype=='text' or ttype=='sblt':
								f.seek(hdlr_pos+16)
								f.write(struct.pack('I', SBTL))
								f.seek(tkhd_pos+40)
								f.write(self.__swapBytes(struct.pack('I', 2)))
								f.seek(tkhd_pos+8)
								if strack: trackflags -= 1
								strack = True
								f.write(self.__swapBytes(struct.pack('I', trackflags)))
							if ttype=='vide':
								f.seek(tkhd_pos+8)
								if vtrack: trackflags -= 1
								vtrack = True
								f.write(self.__swapBytes(struct.pack('I', trackflags)))
								f.seek(tkhd_pos+28)
								d = struct.unpack('I', self.__swapBytes(f.read(4)))[0]
								if d>video_dur: video_dur=d
							if ttype=='soun':
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
					print f.write(self.__swapBytes(struct.pack('I', video_dur)))
			f.seek(pos+moov_sz)
		f.close()

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
		f = open(fn, 'r')
		fs = os.path.getsize(fn)
		gi = (0,'',0)
		while (gi[2]+gi[0])<fs:
			gi = self.__getSectionInfo(f)
			add = [gi[0], gi[1], gi[2], ]
			if gi[1]=='moov':
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
		(sz, name, pos) = si
		fo.seek(0, 2)
		fo.write(self.__swapBytes(struct.pack('I', sz)))
		fo.write('free')
		sz -= 8
		while sz>0:
			fo.write('x')
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
		print addSize
		if addSize==0:
			return None
		fstruct = self.__getFileStruct(fn)
		moovIdx = -1
		mdatIdx = -1
		for i in range(len(fstruct)):
			gi = fstruct[i]
			print '%012d +%s(%d)'%(gi[2], gi[1], gi[0])
			if gi[1]=='moov': moovIdx = i
			if gi[1]=='mdat': mdatIdx = i
		moveMoov = False
		if moovIdx < mdatIdx:
			gi = fstruct[moovIdx+1]
			moveMoov = (gi[1]=='free') and ((gi[0]-8)<addSize)
		print moveMoov
		i = len(fstruct)-1
		while fstruct[i][1]=='free':
			del fstruct[i]
			i-=1
		if moveMoov:
			gi = fstruct[moovIdx]
			gi[1] = 'free'
			add = (gi[0]+addSize, 'moov', gi[2], gi[3])
			fstruct.append(add)
		else:
			for i in [moovIdx-1, moovIdx+1]:
				if i>-1 and i<len(fstruct):
					gi = fstruct[i]
					if gi[1]=='free':
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
			if gi[1]=='free' and streams[-1][1]=='free':
				streams[-1][0] += gi[0]
			else:
				streams.append(gi)

		f = open(fn, 'r')
		of_name = '%s.tmp'%fn.split('/')[-1]
		fo = open(of_name, 'w+')
		trackCounter = 0
		for i in range(len(streams)):
			gi = streams[i]
			print '%012d +%s(%d)'%(gi[2], gi[1], gi[0])
			if gi[1]=='moov':
				fo.write(self.__swapBytes(struct.pack('I', gi[0])))
				fo.write('moov')
				for mi in gi[3]:
					self.__copySection(mi, f, fo)
					if mi[1]=='trak':
						if names[trackCounter]!=None:
							print '%012d   %s(%d)\t%s'%(mi[2], mi[1], mi[0], names[trackCounter])
							nsz = len(names[trackCounter]) + 16
							fo.write(self.__swapBytes(struct.pack('I', nsz)))
							fo.write('udta')
							fo.write(self.__swapBytes(struct.pack('I', nsz-8)))
							fo.write('name')
							fo.write(names[trackCounter])
							fo.seek(-1*(mi[0]+nsz), 2)
							nsz = mi[0]+nsz
							fo.write(self.__swapBytes(struct.pack('I', nsz)))
						else:
							print '%012d   %s(%d)'%(mi[2], mi[1], mi[0])
						trackCounter += 1
					else:
						print '%012d   %s(%d)'%(mi[2], mi[1], mi[0])
			elif gi[1]=='free':
				self.__writeFreeBlock(gi, fo)
				#pass
			else:
				self.__copySection(gi, f, fo)
		f.close()
		fo.close()
		cmd = 'mv "%s" "%s"'%(of_name, fn)
		os.system(cmd)
		return None

if __name__=='__main__':
	if len(sys.argv)==2:
		#mpeg4fixer().fixFlagsAndSubs(sys.argv[1])
		names = [None, None, 'OpenDub', 'Persona99', 'Shachiburi', 'Antravoco', 'Shift', 'Stan WarHammer & Nesitach']
		mpeg4fixer().setTrackNames(sys.argv[1], names)
