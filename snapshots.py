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
	if sys.platform != 'darwin':
		cmd_str = cmd_str.encode('utf-8')
	print cmd_str


if __name__=='__main__':
	if len(sys.argv)==1:
		print 'usage:\n  %s <options> <media files> '%os.path.basename(sys.argv[0])
		print 'where <options>:'
		print '   -c 	<int>	shots count by file'
		print '   -d 	<str>	snapshots directory (default "%s")'%snapshots_dir
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
				cmd = [ffmpeg_path, '-ss', '', '-vframes:v', '1',  '-i', fn, '-y', '-vcodec', 'png', '-an', '-f', 'image2', '']
				while tm < duration:
					cmd[2] = '%.02f'%tm
					cmd[-1] = '%s/%s_%03d_of_%03d.png'%(snapshots_dir, os.path.basename(fn), i, shots_count)
					__print_cmd(cmd)
				
					p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
					while True:
						retcode = p.poll()
						line = p.stdout.readline()
						if retcode is not None and len(line)==0:
							break
					tm += duration/shots_count
					i += 1
