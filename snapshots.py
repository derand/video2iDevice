#!/usr/bin/env python
# -*- coding: utf-8 -*-


__version__ = '0.1'
__author__ = 'Andrey Derevyagin'
__maintainer__ = 'Andrey Derevyagin'
__email__ = '2derand+2idevice@gmail.com'
__copyright__ = 'Copyright © 2010-2012, Andrey Derevyagin'


import os
import sys
from mediaInfo import cMediaInfo, MediaInformer
from constants import *
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
	#	cmd_str = cmd_str.encode('utf-8')
	print cmd_str


if __name__=='__main__':
	if len(sys.argv)==1:
		print 'usage:\n  %s <options> <media files> '%os.path.basename(sys.argv[0])
		print 'where <options>:'
		print '   -c 	<int>		shots count by file'
		print '   -d 	<str>		snapshots directory (default "%s")'%snapshots_dir
		print '   -s 	<int>x<int>	snapshot size, can looks like ("*x320", "960x*"")'
		print '   -f 	<str>		snapshots file format, png(default) or jpeg'
		print '''
Author
	Writed by %s (%s)

Copyright
	%s
  
Bugs
	If you feel you have found a bug in "%s", please email me %s
'''%(__author__, __email__, __copyright__, os.path.basename(sys.argv[0]), __email__)
		sys.exit(0)
	files = []
	i = 1
	_w = 0
	_h = 0
	vcodec = 'png'
	out_ext = 'png'
	while i < len(sys.argv):
		arg = sys.argv[i]
		if arg=='-c':
			i += 1
			shots_count = int(sys.argv[i])
		elif arg=='-d':
			i += 1
			snapshots_dir = sys.argv[i]
			if snapshots_dir[-1]=='/':
				snapshots_dir = snapshots_dir[:-1]
		elif arg=='-s':
			i += 1
			res = sys.argv[i].split('x')
			if res[0]=='*':
				_h =  int(res[1])
			elif res[1]=='*':
				_w = int(res[0])
			else:
				_w = int(res[0])
				_h = int(res[1])
		elif arg=='-f':
			i += 1
			if sys.argv[i].lower()=='jpeg' or sys.argv[i].lower()=='jpg':
				vcodec = 'jpeg'
				out_ext = 'jpg'
		else:
			files.append(arg)
		i += 1
	if not os.path.exists(snapshots_dir):
		os.mkdir(snapshots_dir)
	for fn in files:
		i = 1
		mi = MediaInformer(ffmpeg_path, mkvtoolnix_path, mediainfo_path, AtomicParsley_path, '/tmp/')
		fi = mi.fileInfo(fn)
		if fi.general.has_key('mediaDuration'):
			duration = fi.general['mediaDuration']
			if duration>shots_count:
				tm = duration/(shots_count*2)
				
				cmd = [ffmpeg_path, '-ss', '', '-vframes:v', '1',  '-i', fn, '-y']
				if vcodec=='png':
					cmd.append('-vcodec')
					cmd.append(vcodec)
				elif vcodec=='jpeg':
					cmd.append('-sameq')
				cmd[len(cmd):] = ['-an', '-f', 'image2', '']

				if _w>0 or _h>0:
					stream = fi.video_stream()
					if stream==None:
						print 'Can\'t find video stream at %s'%fn
						sys.exit(1)
					w = stream.params['width']
					h = stream.params['height']
					if stream.params.has_key('dwidth') and stream.params.has_key('dheight'):
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
					cmd[-1] = '%s/%s_%03d_of_%03d.%s'%(snapshots_dir, os.path.basename(fn), i, shots_count, out_ext)
					__print_cmd(cmd)
				
					p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
					while True:
						retcode = p.poll()
						line = p.stdout.readline()
						if retcode is not None and len(line)==0:
							break
					tm += duration/shots_count
					i += 1
