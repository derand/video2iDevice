#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# writed by derand
# - Sorry for horrible code -

# thanks:
#   http://ffmpeg.org/ffmpeg-doc.html
#   http://www.linux.org.ru/forum/desktop/3597304
#   http://theapplegeek.ru/archives/3800
#   http://streaming411.com/wiki/index.php?title=Encoding_prerecorded_video
#   http://atomicparsley.sourceforge.net
#


__version__ = '0.5.4'
__author__ = 'Andrey Derevyagin'
__maintainer__ = 'Andrey Derevyagin'
__email__ = '2derand+2idevice@gmail.com'
__copyright__ = 'Copyright © 2010-2012, Andrey Derevyagin'
#__license__


#####################  #########################

import sys
import os
import re
import getopt
import glob
import string
import json_ex
import os.path
import time
import shutil
import fileCoding
import os.path

#import xml.parsers.expat
from subprocess import Popen, PIPE, STDOUT

from subConverter import subConverter
from mpeg4fixer import mpeg4fixer

import select
import shlex
import codecs

from mediaInfo import cStream, cMediaInfo, cChapter, MediaInformer, isMatroshkaMedia
from v2d_utils import *


STTNGS = {
	'version' : __version__,
#	'threads':	3,
	'files':	[],
	'ac':		True,
	'vc':		True,
	'sc':		True,
	'lang':		'',
	'ar':		48000,
	'ab':		128,
	'b':		960,
	'refs':		2,
	'tn':		False,
	'streams':	'',
	'tfile':	'',
	'fd':		False,
	'fadd':		[],
	'format':	'm4v',
	'add2TrackIdx': 0,
	'vcodec':	'libx264',
	'vcopy':	False,
	'acopy':	False,
	'vr':		23.976,
	'ctf':		False,
	'vv':		False,
	'web_optimization': True,
	'temp_dir': '.',
	'encodingTool': '2iDevice',
	'cast': 			[],
	'directors':		[],
	'producers':		[],
	'codirectors':		[],
	'screenwriters':	[],
	'sleep_between_files': 0,
}

atomicParsleyOptions = ('artist', 'title', 'album', 'genre', 'tracknum', 'disk', 'comment', 'year', 'lyrics', 'lyricsFile', 'composer',
 'copyright', 'grouping', 'artwork', 'bpm', 'albumArtist', 'compilation', 'hdvideo', 'advisory', 'stik', 'description', 'longdesc',
 'storedesc', 'TVNetwork', 'TVShowName', 'TVEpisode', 'TVSeasonNum', 'TVEpisodeNum', 'podcastFlag', 'category', 'keyword', 'podcastURL',
 'podcastGUID', 'purchaseDate', 'encodedBy', 'apID', 'cnID', 'geID', 'xID', 'gapless', 'contentRating', 'Rating')

help = '''
Converter video for iPhone/iPod Touch/iPad
for work script you should install ffmpeg with x264 codec (http://blog.derand.net/2009/06/ffmpeg-x264.html),
MP4Box (http://gpac.sourceforge.net/doc_mp4box.php)
AtomicParsley (http://atomicparsley.sourceforge.net)
mkvtoolnix (http://www.bunkus.org/videotools/mkvtoolnix/downloads.html)
Usage
  ./2iDevice.py [options] inputFile[s]

Global options:
	-h			this help
	-th		[int]	using threads for coding
	-lang		[str]	languages of srteams separated ':' (also can set for each track like 'stream' param)
	-cn			disable converting step (files converted yet from another script run), merge streams files to .m4v file
	-streams	[str]	select streams numbers or 'none' for none (first index 0 separated ':', default 'all')
				also index can be formated [stream_type]_[stream index or stream language] where:
					stream_type - symbol (v - video, a - audio, s - subtitle)
					stream index - stream number, counting only for this type streams
					stream language - search stream by language
	-tfile		[str]	set tags file
	-TRACK_REGEX	[srt]	set regular exeption for select track number from filename
	-TRACKS_REGEX	[srt]	set regular exeption for select tracks count from filename
	-out_file	[str]	save result to this file. supports tags: [SEASON], [EPISODE_ID]
	-out_path	[str]	save result to this directory
	-format		[str]	output format, can be: mp4, m4v, mkv (default: 'm4v')
	-stream		[int]	stream idx from appending files, like streams param, only one index
	-ctf			clear temp files after converting
	-v			script version
	-copy			copy selected stream from source
	-delay		[int]	sets track start delay in ms.
	-info 		[str]	show media file info, value is format (can be blank), 'json' - JSON format, 'short' - short human format, default - human format
	-info1 			synonim for '-info short'
	-vv			verbose mode
	-temp_dir	[str]	path to temporary directory
	-ffmpeg_coding_params	[str]	add ffmpeg params for video/audio coding (set's for selected stream), video filters disabled
	-json_pipe		set all params by JSON array [] in pipe, this should be only one param on parameters
	-web_optimization	[int]	optimization result file to streaming (0 - disabled, another - enabled(default))
	-stream_prefix	[str]	stream percentage prefix (shows when converting stream)
	-log_file 		[srt]	set log file
	-ss 		[str]	split media file, format: HH:MM:SS.ms/HH.MM.SS.ms 
				where first - start time, second - duration (not required)
				Use "tagging_mode" for split only
	-sleep_between_files	[int]	pause between encoding files
	-test_mode		test mode, show only commands and don't execute them (default: disabled)
	-vcodec  [string]	video codec (libx264 - default)

Video options:
	-vfile		[str]	set video filename. If not set try search in current dir. 
				Can be format:
					[NAME] - origin name of file
					[2EID] - episode id (evaluate from regext in tfile)
					[2EC] - episode count
	-b		[int]	video bitrate (def 960)
	-crf 		[int]	one pass coding, crf param
	-refs		[int]	ref frames for coding video
	-fd			fix video duration
	-s		[int]x[int]	result resolution, can looks like ('*x320', '960x*')
	-passes  	[str]	video passes coding separeted ':' (use for non crf mode)
	-vr        	[float]	frame rate (default 23.976)
	-crop	[int]:[int]:[int]:[int]	crop video (width:height:x:y)
	-vcopy			copy video stream from source
	-vn			disable convert video

Audio options:
	-afile		[str]	set audio filename. If not set try search in current dir. 
				Can be format:
					[NAME] - origin name of file
					[2EID] - episode id (evaluate from regext in tfile)
					[2EC] - episode count
	-ar		[int]	audio frequency (def 48000)
	-ab		[int]	audio bitrate (def 128k)
	-avol		[int]	change audio volume (def 256=100%), only for 'afile' params
	-acopy			copy audio stream from source
	-an			disable convert audio

Subtitle options:
	-sfile		[str]	set subtitle filename. If not set try search in current dir. 
				Can be format:
					[NAME] - origin name of file
					[2EID] - episode id (evaluate from regext in tfile)
					[2EC] - episode count
	-hardsub		set stream as hurdsub (for ass format only)
	-sn			disable convert subtitles
	-addTimeDiff 	[int]	add time(ms) diff to subs (last sub stream)

Tagging options:
	-tagging_mode		set tags only
	-track		[int]	track
	-tracks		[int]	tracks count
	-et		[str]	set episodes titles separated ';' (for TV Shows)
	-sname		[srt]	stream title from appending files (vfile, afile, sfile)
	-add2TrackIdx	[int]	add to track (def: 0)
	-copy_warning 	[str]	Add copy warning (displayed in iTunes summary page)
	-studio 	[str]	Add film studio (displayed on Apple TV)
	-cast 		[str]	Add Actors (displayed on Apple TV and iTunes under long description)
	-directors	[str]	Add Directors (displayed on Apple TV and iTunes under long description)
	-producers	[str]	Add Producers (displayed on Apple TV and iTunes under long description)
	-codirectors 	[str]	Add Co-Directors (displayed in iTunes under long description)
	-screenwriters 	[str]	Add ScreenWriters (displayed in iTunes under long description)
	-tn			disable sets tags
For tagging you can use AtomicParsley long-option params (see "AtomicParsley -h"), in param use one '-' symbol like:
	./2iDevice.py <filename> -contentRating Unrated
for AtomicParsley --contentRating Unrated.

	
Author
	Writed by Andrey Derevyagin (2derand+2idevice@gmail.com)

Copyright
	Copyright © 2010-2012 Andrey Derevyagin
  
Bugs
	If you feel you have found a bug in "2iDevice", please email me 2derand+2idevice@gmail.com
'''

#black_list = ('EdKara', 'TVLpaint', 'SerialMainTitle', 'Kar_OP_1', 'Kar_OP_2', 'Kar_OP_3', 'Kar_OP_4', 'Kar_ED_1', 'Kar_ED_2', 'Kar_ED_3', 'Kar_ED_4', 'Kar_ED_5', 'Kar_ED_6' )


if sys.platform == 'darwin':
	os_ffmpeg_prms = []
else:
	#os_ffmpeg_prms = ['-flags2', '+bpyramid-mixed_refs+wpred+dct8x8+fastpskip']
	os_ffmpeg_prms = []





class LogToFile(object):
	"""docstring for LogToFile"""
	def __init__(self):
		super(LogToFile, self).__init__()
		self.__log_file = None
		self.__file_name = None

	def __del__(self):
		self.releaseLog()

	def put(self, text, flush=True):
		if self.__log_file<>None:
			self.__log_file.write(text)
			if flush:
				self.flush()

	def flush(self):
		if self.__log_file<>None:
			self.__log_file.flush()		

	def isSetted(self):
		return self.__log_file<>None

	def file_name(self):
		return self.__file_name

	def initLogByFileName(self, logFileName):
		self.releaseLog()
		self.__file_name = logFileName
		self.__log_file = open(logFileName, 'w')

	def releaseLog(self):
		if self.__log_file<>None:
			self.__log_file.close()
			self.__log_file = None



class Video2iDevice(object):
	"""docstring for Video2iDevice"""
	def __init__(self):
		super(Video2iDevice, self).__init__()
		self.mediainformer = MediaInformer(ffmpeg_path=ffmpeg_path, mkvtoolnix_path=mkvtoolnix_path, mediainfo_path=mediainfo_path, atomicParsley_path=AtomicParsley_path, mp4box_path=mp4box_path, artwork_path=STTNGS['temp_dir'])
		self.log = LogToFile()
		self.__iTunMOVI_arrayKeys = ['cast', 'directors', 'producers', 'codirectors', 'screenwriters']

	def getSettings(self, argv):
		ckey = 'files'
		saveP = False
		waitParam = False
		for el in argv:
			if len(el)>0 and el[0]=='-' and not waitParam:
				ckey = el[1:]
				if ckey=="th":
					ckey='threads'
				if ckey=="et":
					ckey='episodes_titles'
				saveP = False
				if ckey=='nconvert' or ckey=='cn':
					STTNGS['ac'] = False
					STTNGS['vc'] = False
					STTNGS['sc'] = False
					saveP = True
				if ckey=='vn':
					STTNGS['vc'] = False
					saveP = True
				if ckey=='an':
					STTNGS['ac'] = False
					saveP = True
				if ckey=='sn':
					STTNGS['sc'] = False
					saveP = True
				# stream and global single params
				if ckey=='vcopy' or ckey=='acopy':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1]['copy'] = True
					else:
						STTNGS[ckey] = True
					saveP = True
				# stream single params
				if ckey=='copy' or ckey=='hardsub':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1][ckey] = True
					saveP = True
				# global single params
				if ckey=='tn' or ckey=='fd' or ckey=='ctf' or ckey=='vv' or ckey=='tagging_mode' or ckey=='test_mode':
					STTNGS[ckey] = True
					saveP = True
				# params that can be started from '-' symbol
				if ckey=='addTimeDiff' or ckey=='add2TrackIdx' or ckey=='ffmpeg_coding_params':
					waitParam = True
				# help param or wrong
				if ckey=='h' or ckey=='json_pipe':
					print help
					sys.exit(0)
				# version param
				if ckey=='v':
					print "Version: %s"%STTNGS['version']
					sys.exit(0)
				# single or not param 
				if ckey=='info':
					STTNGS[ckey] = None
				if ckey=='info1':
					STTNGS['info'] = 'short'
					saveP = True
			else:
				waitParam = False
				if saveP:
					ckey = 'files'
				if ckey=='vfile' or ckey=='afile' or ckey=='sfile':
					tt=2
					if ckey=='afile': tt=1
					if ckey=='vfile': tt=0
					STTNGS['fadd'].append((tt, el, {}))
				elif ckey=='episodes_titles' or ckey=='TRACK_REGEX' or ckey=='TRACKS_REGEX':
					STTNGS[ckey] = el.split(';')
				elif ckey=='stream':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1]['stream'] = el
				elif ckey=='sname':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1]['sname'] = el
				elif ckey=='ar' and len(STTNGS['fadd'])>0:
					tmp = STTNGS['fadd']
					tmp[-1][-1]['ar'] = int(el)
				elif ckey=='ab' and len(STTNGS['fadd'])>0:
					tmp = STTNGS['fadd']
					tmp[-1][-1]['ab'] = int(el)
				elif ckey=='addTimeDiff' and len(STTNGS['fadd'])>0:
					tmp = STTNGS['fadd']
					if tmp[-1][0]==2:
						tmp[-1][-1]['addTimeDiff'] = int(el)
				elif ckey=='avol':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1]['vol'] = el
				elif ckey=='delay':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1]['delay'] = int(el)
				elif ckey=='lang':
					tmp = STTNGS['fadd']
					if string.find(el, ':')==-1 and len(tmp)>0:
						tmp[-1][-1]['lang'] = el
					else:
						STTNGS[ckey] = el
				elif ckey=='crf':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1]['crf'] = el
					else:
						STTNGS[ckey] = el
				elif ckey=='ffmpeg_coding_params':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1][ckey] = shlex.split(el)
				elif ckey=='web_optimization':
					STTNGS[ckey] = el<>'0'
				elif ckey=='stream_prefix':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1][ckey] = el
				elif ckey in self.__iTunMOVI_arrayKeys:
					for tmp in el.split(','):
						STTNGS[ckey].append(tmp.strip())
				elif ckey=='threads':
					STTNGS[ckey] = int(el)
				elif ckey == 'vcodec':
					STTNGS[ckey] = el
				else:
					if STTNGS.has_key(ckey):
						if type(STTNGS[ckey])==type([]):
							STTNGS[ckey].append(el)
						elif type(STTNGS[ckey])==type(123):
							STTNGS[ckey] = int(el)
						elif type(STTNGS[ckey])==type(1.23):
							STTNGS[ckey] = float(el)
						else:
							STTNGS[ckey] = el
							'''
							if ckey=='format':
								STTNGS[ckey] = el
							else:
								STTNGS[ckey] += el
							'''
					else:
						STTNGS[ckey] = el
				saveP = True
		if STTNGS['vv']:
			print STTNGS


	def loadSettingsFile(self, filename):
		file = 0 
		try:
			encoding = fileCoding.file_encoding(filename)
			file = codecs.open(filename, mode='r', encoding=encoding)
		except:
			print 'error open file %s'%filename
			sys.exit(1)
		inside_key = False
		save_key = ''
		_tmp = ''
		rv = {}
		arrSymb = None
		file_lines = file.read().encode('utf-8')
		for line in file_lines.split('\n'):
			if len(line)<1 or line[0]=='#':
				continue
			if inside_key:
				_tmp += line.strip()
				if _tmp[-1]==arrSymb:
					if inside_key:
						if STTNGS['vv']:
							print _tmp
						#rv[save_key] = json.loads(_tmp)
						rv[save_key] = json_ex.JsonReader().read(_tmp)
						inside_key = False
			else:
				tmp = line.split('=',1)
				if len(tmp)!=2:
					continue
				(key, val) = (tmp[0].strip(), tmp[1].strip())
				if val[0]=='[' or val[0]=='{':
					if val[0]=='[': arrSymb=']'
					if val[0]=='{': arrSymb='}'
					if val[-1]==arrSymb:
						#rv[key] = json.loads(_tmp)
						rv[key] = json_ex.JsonReader().read(val)
					else:
						save_key  =key
						_tmp = val
						inside_key = True
				else:
					if key in self.__iTunMOVI_arrayKeys:
						for tmp in val.split(','):
							STTNGS[key].append(tmp.strip())
					rv[key] = val
		return rv

	def __printCmd(self, cmd):
		print ': \033[1;32m%s\033[00m'%cmd
		self.log.put('\n: \033[1;32m%s\033[00m\n'%cmd, True)

	def __exeFfmpegCmd(self, params, percentagePrefix=None):
		def timeToMs(hoursMinsSecMs_array):
			hours = int(hoursMinsSecMs_array[0])
			mins = int(hoursMinsSecMs_array[1])
			secs = int(hoursMinsSecMs_array[2])
			ms = int(hoursMinsSecMs_array[3])
			return ((hours*60 + mins)*60 + secs)*100 + ms

		cmd = [ffmpeg_path, ]
		#cmd[len(cmd):] = params
		for prm in params:
			if prm[0]=='"' and prm[-1]=='"':
				cmd.append(prm[1:-1])
			else:
				cmd.append(prm)
		cmd_str = add_separator_to_filepath(cmd[0])
		for i in range(1,len(cmd)):
			if cmd[i].find(' ')==-1:
				cmd_str += ' %s'%cmd[i]
			else:
				cmd_str += ' "%s"'%cmd[i]
		#if sys.platform != 'darwin':
		#	cmd_str = cmd_str.encode('utf-8')
		self.__printCmd(cmd_str)
		if STTNGS.get('test_mode'):
			return (0, None, None)
		#cmd = ['/Users/maliy/work/Video to iDevice/video2iDevice/binary/ffmpeg', '-y', '-i', '/Users/maliy/Movies/Ga-Rei Zero/Ga-Rei Zero - 04 (BDRip H264 1280x720)_0_30.mp4', '-map', '0:0', '-an', '-vcodec', 'libx264', '-crf', '18.2', '-s', '1280x720', '-refs', '6', '-threads', '4', '-partitions', '+parti4x4+parti8x8+partp4x4+partp8x8+partb8x8', '-subq', '12', '-trellis', '1', '-coder', '1', '-me_range', '32', '-level', '4.1', '-profile:v', 'high', '-bf', '12', '-r', '23.976', '/tmp/VideoToIDevice/Ga-Rei Zero - 04 (BDRip H264 1280x720)_0_30.mp4_0:0.mp4']
		#cmd = ['/Users/maliy/work/Video to iDevice/video2iDevice/binary/ffmpeg', '-y', '-i', '/Users/maliy/Movies/Hatsune Miku & Megurine Luka – 39′s Giving Day.m4v', '-map', '0:0', '-an', '-vcodec', 'libx264', '-crf', '18', '-s', '1280x720', '-refs', '6', '-threads', '4', '-partitions', '+parti4x4+parti8x8+partp4x4+partp8x8+partb8x8', '-subq', '12', '-trellis', '1', '-coder', '1', '-me_range', '32', '-level', '4.1', '-profile:v', 'high', '-bf', '12', '-r', '23.976', '/tmp/VideoToIDevice/Ga-Rei Zero - 04 (BDRip H264 1280x720)_0_30.mp4_0:0.mp4']
		p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
		retcode = 0
		line = ''
		duration = None
		duration_re_compiled = re.compile('Duration:\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})')
		time = 0
		time_re_compiled = re.compile('.*time=\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})')
		libx264_log_settings = []
		libx264_log = []

		tmp_process_catched = False
		tmp_line = None
		while True:
			retcode = p.poll() #returns None while subprocess is running
			#print p.stdout, p.stderr
			ch = p.stdout.read(1)
			if ch=='\r' or ch=='\n':
				line = line.strip()
				process_catched = False
				if duration==None:
					duration_re =  duration_re_compiled.search(line)
					if duration_re:
						duration = float(timeToMs(duration_re.groups()))
				else:
					#frame=  491 fps= 20 q=23.0 size=    2228kB time=00:00:18.01 bitrate=1013.0kbits/s dup=2 drop=0
					time_re =  time_re_compiled.search(line)
					process_catched = time_re<>None
					if time_re:
						time = timeToMs(time_re.groups()[0:4])
						try:
							if time>duration:
								time = duration
						except Exception, e:
							p.kill()
							raise e
					if line[:len('[libx264')]=='[libx264':
						if time==0:
							libx264_log_settings.append(line)
						else:
							libx264_log.append(line)
				s = ''
				line = line
				if STTNGS['vv']:
					s = line
				else:
					if process_catched:
						if percentagePrefix<>None:
							s = percentagePrefix
						s += '  %.2f%% %s   '%(float(time)*100.0/float(duration), line)
					elif tmp_process_catched:
						if percentagePrefix<>None:
							s = percentagePrefix
						s += '  %.2f%% %s   '%(float(duration)*100.0/float(duration), tmp_line)
				if len(s):
					sys.stdout.write(s+ch)
					sys.stdout.flush()
				if ch=='\n':
					if tmp_line<>None and tmp_line[-1]=='\r':
						self.log.put(tmp_line, False)
					self.log.put(line+ch, True)
				#print line
				
				tmp_process_catched = process_catched
				tmp_line = line+ch

				line = ''
			else:
				line += ch
			if retcode is not None and not STTNGS['vv']:
				print
				for l in libx264_log_settings:
					print l
				if len(libx264_log_settings)>0 and len(libx264_log):
	 				print '--- h264 log ---'
				for l in libx264_log:
					print l
				break
		if retcode<>0:
			print cmd
			sys.exit()
		return (retcode, libx264_log, libx264_log_settings)

	def __exeCmd(self, cmd, check_exit_code=True):
		cmd_str = add_separator_to_filepath(cmd[0])
		print cmd
		for i in range(1,len(cmd)):
			if cmd[i].find(' ')==-1:
				cmd_str += ' %s'%cmd[i]
			else:
				cmd_str += ' "%s"'%cmd[i]
		#if sys.platform != 'darwin':
		#	cmd_str = cmd_str.encode('utf-8')
		self.__printCmd(cmd_str)
		if STTNGS.get('test_mode'):
			return 0
		p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
		line = ''
		tmp_line = None
		retcode = 0
		while True:
			retcode = p.poll()
			ch = p.stdout.read(1)
			if ch=='\r' or ch=='\n':
				#line = line.strip()
				sys.stdout.write(line+ch)
				if ch=='\n':
					if tmp_line<>None and tmp_line[-1]=='\r':
						self.log.put(tmp_line, False)
					self.log.put(line+ch, True)
				tmp_line = line+ch
				line = ''
			else:
				line += ch
			if retcode is not None and len(ch)==0:
				break
		if check_exit_code and retcode<>0:
			print cmd
			print 'Exit code: %d'%retcode
			sys.exit()
		return retcode


	def getLang(self, i, lng=None):
		langs = STTNGS['lang'].split(':')
		if len(langs)>i and langs[i]!='':
			return (langs[i],i+1)
		if lng==None or lng=='':
			return ('und', i+1)
		return (lng, i+1)

	def tagTrackInfo(self, fn):
		srch = None
		tr = None
		rv = {}
		if STTNGS.has_key('track'):
			tr = int(STTNGS['track'])
		if STTNGS.has_key('TRACK_REGEX'):
			for p in STTNGS['TRACK_REGEX']:
				srch = re.compile(p).search(fn)
				if srch!=None:
					break
			if srch!=None:
				tr = int(srch.groups()[0])+STTNGS['add2TrackIdx']
		rv['track'] = tr
		trs = None
		if STTNGS.has_key('tracks'):
			trs = int(STTNGS['tracks'])
		if STTNGS.has_key('TRACKS_REGEX'):
			for p in STTNGS['TRACKS_REGEX']:
				srch = re.compile(p).search(fn)
				if srch!=None:
					break
			if srch!=None:
				trs = int(srch.groups()[0])
		rv['tracks'] = trs
		if tr==None and not rv.has_key('season'):
			srch = re.compile('[sS](\d{2})[eE](\d{2})').search(fn)
			if srch!=None:
				tr = int(srch.groups()[1])+STTNGS['add2TrackIdx']
				rv['track'] = tr
				rv['season'] = int(srch.groups()[0])
		return rv

	def __has_iTunMOVI(self):
		rv = STTNGS.has_key('copy_warning') or STTNGS.has_key('studio')
		for key in self.__iTunMOVI_arrayKeys:
			rv = rv or len(STTNGS[key])>0
		return rv

	def __iTunMOVI_XML(self):
		rv = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE plist PUBLIC \"-//Apple Computer//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n<plist version=\"1.0\">\n  <dict>\n"""
		if STTNGS.has_key('copy_warning'):
			rv += "    <key>copy-warning</key>\n    <string>%s</string>\n"%STTNGS['copy_warning']

		if STTNGS.has_key('studio'):
			rv += "    <key>studio</key>\n    <string>%s</string>\n"%STTNGS['studio']

		for tag in self.__iTunMOVI_arrayKeys:
			if len(STTNGS[tag])>0:
				rv += "    <key>%s</key>\n    <array>\n"%tag
				for name in STTNGS[tag]:
					rv += "      <dict>\n        <key>name</key>\n        <string>%s</string>\n      </dict>\n"%name
				rv += "    </array>\n"

		rv += "  </dict>\n</plist>\n"
		return rv


	def iTagger(self, fn):
		if not STTNGS['tn']:
			#prms = ' --copyright "derand"'
			prms = {
				'encodingTool': STTNGS['encodingTool'],
				#'overWrite': ''
			}
			info = self.tagTrackInfo(fn)
			for option in atomicParsleyOptions:
				if STTNGS.has_key(option):
					#prms[option] = ' "%s"'%STTNGS[option]
					prms[option] = STTNGS[option]
				#prms = __add_param(STTNGS, '--%s'%option, option, prms)

			(track, tracks) = (info['track'], info['tracks'])
			if track!=None:
				if tracks!=None:
					#prms += ' --tracknum %d/%d --TVEpisodeNum %d'%(track, tracks, track)
					prms['tracknum'] = '%d/%d'%(track, tracks)
					prms['TVEpisodeNum'] = '%d'%track
				else:
					#prms += ' --tracknum %d --TVEpisodeNum %d'%(track, track)
					prms['tracknum'] = '%d'%track
					prms['TVEpisodeNum'] = '%d'%track
				if STTNGS.has_key('episodes_titles') and len(STTNGS['episodes_titles'])>(track-1):
					title = '%s'%STTNGS['episodes_titles'][track-1].replace("`", '_')
					#prms += ' --TVEpisode %s'%title
					#prms += ' --title %s'%title
					prms['TVEpisode'] = title
					prms['title'] = title
				elif STTNGS.has_key('episodes') and len(STTNGS['episodes'])>(track-1):
					epInfo = STTNGS['episodes'][track-1]
					for option in atomicParsleyOptions:
						if epInfo.has_key(option):
							if option=='title':
								prms['TVEpisode'] = '%s'%epInfo[option]
							prms[option] = '%s'%epInfo[option]
				else:
					#prms += ' --TVEpisode "%s"'%fn
					title = os.path.basename(fn)
					title = os.path.splitext(title)[0]
					prms['TVEpisode'] = '%s'%title

			cmd = [AtomicParsley_path, fn, ]
			for p in prms.keys():
				cmd.append('--%s'%p)
				cmd.append(prms[p])
			if self.__has_iTunMOVI():
				xml = self.__iTunMOVI_XML()
				cmd.append('--rDNSatom')
				cmd.append(xml)
				cmd.append('name=iTunMOVI')
				cmd.append('domain=com.apple.iTunes')
			cmd.append('--overWrite')
			self.__exeCmd(cmd)

			#if self.__has_iTunMOVI():
			#	xml = self.__iTunMOVI_XML()
			#	cmd = [AtomicParsley_path, fn, '--rDNSatom', xml, 'name=iTunMOVI', 'domain=com.apple.iTunes', '--overWrite']
			#	self.__exeCmd(cmd)

			###prms += ' --encodingTool "2iDevice.py (http://blog.derand.net)" --overWrite'
			#prms_str = ''
			#for p in prms.keys():
			#	if prms[p].find(' ')==-1 or (prms[p][0]=='\"' and prms[p][-1]=='\"' and prms[p].count('\"')==2):
			#		prms_str += ' --%s %s'%(p, prms[p])
			#	else:
			#		prms_str += ' --%s "%s"'%(p, prms[p])
			#cmd = AtomicParsley_path + ' "%s" %s --overWrite'%(unicode(fn,'UTF-8'), unicode(prms_str, 'UTF-8'))
			#self.__printCmd(cmd.encode('utf-8'))
			#os.system(cmd.encode('utf-8'))

	def buildFN(self, baseFN, convertFN):
		rv = convertFN
		if rv.find('[NAME]')>-1:
			nm = '.'.join(os.path.basename(baseFN).split('.')[:-1])
			rv = rv.replace('[NAME]', nm)
		info = self.tagTrackInfo(baseFN)
		(track, tracks) = (info['track'], info['tracks'])
		if rv.find('[2EID]')>-1:
			if track!=None:
				rv = rv.replace('[2EID]', '%02d'%track)
		if rv.find('[2EC]')>-1:
			if tracks!=None:
				rv = rv.replace('[2EC]', '%02d'%tracks)
		return rv

	def rename(self, fn):
		if not STTNGS.has_key('out_file'):
			return None
		name = STTNGS['out_file']
		info =  self.tagTrackInfo(fn)
		(tr, trs) = (info['track'], info['tracks'])
		if name.find('[SEASON]')>-1:
			if STTNGS.has_key('TVSeasonNum'):
				name = name.replace('[SEASON]', STTNGS['TVSeasonNum'])
		if name.find('[EPISODE_ID]')>-1:
			if tr!=None:
				name = name.replace('[EPISODE_ID]', '%02d'%tr)
		if name.find('[EPISODE_COUNT]')>-1:
			if trs!=None:
				name = name.replace('[EPISODE_COUNT]', '%02d'%trs)
		if name.find('[NAME]')>-1:
			if tr!=None:
				if STTNGS.has_key('episodes_titles') and len(STTNGS['episodes_titles'])>(tr-1):
					name = name.replace('[NAME]', STTNGS['episodes_titles'][tr-1])
		#cmd = 'mv "%s" "%s"'%(fn, name)
		#self.__printCmd(cmd)
		#os.system(cmd)
		self.__printCmd('mv "%s" "%s"'%(fn, name))
		shutil.move(fn, name)

	def __videoFfmpegParamsBase(self, fileName, _map):
		rv =  ['-y', 
				'-i', '"'+fileName+'"',
				'-map_chapters', '-1']
		if _map is not None:
			rv.append('-map')
			rv.append(_map)
		return rv

	def __videoFfmpegParamsCopy(self, fileName, _map):
		rv = self.__videoFfmpegParamsBase(fileName, _map)
		rv[len(rv):] = ['-vcodec', 'copy']
		return rv

	def __videoFfmpegParamsPasses(self, fileName, _map, _pass):
		rv = self.__videoFfmpegParamsBase(fileName, _map)
		add = []
		if _pass is not None:
			add.append('-pass')
			add.append('%s'%_pass)
		add.extend(['-vcodec', STTNGS['vcodec'],
				'-flags', '+loop',
				'-cmp','chroma',
				'-me_method','full'])
		rv[len(rv):] = add
		return rv

	def __videoFfmpegParamsCRF(self, fileName, _map, crf):
		rv = self.__videoFfmpegParamsBase(fileName, _map)
		add = ['-vcodec', STTNGS['vcodec'],
			   '-crf', '%s'%crf]
		rv[len(rv):] = add
		return rv

	def __videoFfmpegParamsQuality(self, fileName, _map, crf=0, _pass=0, hQuality=True):
		if  crf<>0:
			'CRF mode'
			ffmpeg_params = self.__videoFfmpegParamsCRF(fileName, _map, crf)
			ffmpeg_params_add = [#'-s', '%dx%d'%(_w,_h),
								 '-refs', '%d'%STTNGS['refs'],
								 '-threads', '%s'%STTNGS['threads']]
		else:
			'PASSES mode'
			ffmpeg_params = self.__videoFfmpegParamsPasses(fileName, _map, _pass)
			ffmpeg_params_add = ['-b:v', '"%d k"'%STTNGS['b'],
								 #'-s', '%dx%d'%(_w,_h),
								 '-maxrate', '"%d k"'%STTNGS['b'],
								 '-bufsize', '"%d k"'%int(STTNGS['b']*2.5),
								 '-refs', '%d'%STTNGS['refs'],
								 '-threads', '%s'%STTNGS['threads']]
			ffmpeg_params_add[len(ffmpeg_params_add):] = os_ffmpeg_prms
		ffmpeg_params[len(ffmpeg_params):] = ffmpeg_params_add
		ffmpeg_params_add = []
		if hQuality:
			''' HIGHT QUALITY '''
			ffmpeg_params_add = ['-partitions', '+parti4x4+parti8x8+partp4x4+partp8x8+partb8x8',
								 '-subq', '12',
								 '-trellis','1',
								 '-coder', '1',
								 '-me_range', '32',
								 '-level', '4.1',
								 '-profile:v', 'high',
								 '-bf', '12']
			#cmd = ffmpeg_path + ' -y -i "%s" -pass %d -map %s -an  -vcodec "libx264" -b:v "%d k" -s "%dx%d" -flags "+loop" -cmp "+chroma" -partitions "+parti4x4+parti8x8+partp4x4+partp8x8+partb8x8" -subq 12  -trellis 0  -refs %d  -coder 1  -me_range 32  -g 240   -keyint_min 25  -sc_threshold 40 -i_qfactor 0.71 -maxrate  "%d k" -bufsize "%d k" -rc_eq "blurCplx^(1-qComp)" -qcomp 0.6 -me_method full  -b_strategy 1 %s -level 4.1 -threads %d -profile high -bf 10 '%(iFile, _pass, stream[1], STTNGS['b'], _w,_h, STTNGS['refs'], STTNGS['b'], STTNGS['b']*2, os_ffmpeg_prms, STTNGS['threads'])
		else:
			''' LOW QUALITY '''
			ffmpeg_params_add = ['-partitions', '+parti4x4+partp8x8+partb8x8',
								 '-subq', '6',
								 '-trellis','0',
								 '-coder', '0',
								 '-me_range', '16',
								 '-level', '3.1',
								 '-profile:v', 'baseline']
			#cmd = ffmpeg_path + ' -y -i "%s" -pass %d -map %s -an  -vcodec "libx264" -b:v "%d k" -s "%dx%d" -flags "+loop" -cmp "+chroma" -partitions "+parti4x4+partp8x8+partb8x8" -subq 6  -trellis 0  -refs %d  -coder 0  -me_range 16  -g 240   -keyint_min 25  -sc_threshold 40 -i_qfactor 0.71 -maxrate  "%d k" -bufsize "%d k" -rc_eq "blurCplx^(1-qComp)" -qcomp 0.6 -me_method full -b_strategy 1 %s -level 3.1 -threads %d -profile baseline '%(iFile, _pass, stream[1], STTNGS['b'], _w,_h, STTNGS['refs'], STTNGS['b'], STTNGS['b']*2.5, os_ffmpeg_prms, STTNGS['threads'])
		ffmpeg_params[len(ffmpeg_params):] = ffmpeg_params_add
		return ffmpeg_params

	def __mergeFfmpegParams(self, current_params, user_params):
		while len(user_params):
			idx = -1
			param = user_params[0]
			del user_params[0]
			if param[0]=='-':
				val = None
				try:
					idx = current_params.index(param)
				except Exception, e:
					pass
				if user_params[0][0]!='-':
					val = user_params[0]
					del user_params[0]
				if param!='-vf':
					if idx==-1:
						current_params.insert(-1, param)
						if val!=None:
							current_params.insert(-1, val)
					else:
						if val!=None:
							current_params[idx+1] = val
		return current_params

	def __copyFileAndChangeEncoding(self, fn_src, fn_dest):
		fCoding = fileCoding.file_encoding(fn_src)
		if fCoding.lower()=='utf-8':
			shutil.copyfile(fn_src, fn_dest)
		else:
			BLOCKSIZE = 1024*10
			with codecs.open(fn_src, 'r', fCoding) as sourceFile:
				with codecs.open(fn_dest, 'w', 'utf-8') as destFile:
					while True:
						contents = sourceFile.read(BLOCKSIZE)
						if not contents:
							break
						destFile.write(contents)			

	def __prepareHardsubFile(self, hardsub_stream):
		fn = hardsub_stream.params['filename']
		_, file_ext = os.path.splitext(fn)
		file_ext = file_ext.lower()
		ass_fn = None
		if file_ext=='.ass' or file_ext=='.ssa':
			ass_fn = '%s/%s'%(STTNGS['temp_dir'], os.path.basename(fn))
			#shutil.copyfile(fn, ass_fn)
			self.__copyFileAndChangeEncoding(fn, ass_fn)
		elif isMatroshkaMedia(fn) and hardsub_stream.params.has_key('mkvinfo_trackNumber'):
			if hardsub_stream.format().upper()=='ASS' or hardsub_stream.format().upper()=='SSA':
				ass_fn = '%s/%s.%s'%(STTNGS['temp_dir'], os.path.basename(fn), hardsub_stream.format().lower())
				#cmd = mkvtoolnix_path + 'mkvextract tracks "%s" %s:"%s"'%(fn, hardsub_stream.params['mkvinfo_trackNumber'], ass_fn)
				#self.__printCmd(cmd)
				#p = os.popen(cmd)
				#p.close()
				cmd = [mkvtoolnix_path + 'mkvextract', 'tracks', fn, '%s:%s'%(hardsub_stream.params['mkvinfo_trackNumber'], ass_fn)]
				self.__exeCmd(cmd)
			elif hardsub_stream.format().upper()=='SRT':
				srt_fn = '%s/%s.srt'%(STTNGS['temp_dir'], os.path.basename(fn))
				cmd = [mkvtoolnix_path + 'mkvextract', 'tracks', fn, '%s:%s'%(hardsub_stream.params['mkvinfo_trackNumber'], srt_fn)]
				self.__exeCmd(cmd)

				ass_fn = '%s/%s.ass'%(STTNGS['temp_dir'], os.path.basename(fn))
				cmd = ['-y', '-i', srt_fn, ass_fn]
				self.__exeFfmpegCmd(cmd)
		elif file_ext=='.srt':
				ass_fn = '%s/%s.ass'%(STTNGS['temp_dir'], os.path.basename(fn))
				cmd = ['-y', '-i', fn, ass_fn]
				self.__exeFfmpegCmd(cmd)
		else:
			# TODO: there can be added other subtitle format
			return None

		#ass_fn = add_separator_to_filepath(ass_fn)
		#ass_fn = ass_fn.replace('(', '\\(').replace(')', '\\)').replace(' ', '\\ ').replace('[', '\\[').replace(']', '\\]')
		return ass_fn


	def cVideo(self, iFile, stream, oFile):
		print stream.params
		w = stream.params['width']
		h = stream.params['height']
		if stream.params.has_key('dwidth') and stream.params.has_key('dheight'):
			w = stream.params['dwidth']
			h = stream.params['dheight']
	
		if STTNGS.has_key('s'):
			res = STTNGS['s'].split('x')
			if res[0]=='*':
				(_h, _w) = video_size_convert(h, w, int(res[1]))
			elif res[1]=='*':
				(_w, _h) = video_size_convert(w, h, int(res[0]))
			else:
				_w = int(res[0])
				_h = int(res[1])
		else:
			(_w, _h) = (w, h)
			#(_w, _h) = video_size_convert(w, h, w)
			#(_h, _w) = video_size_convert(_h, _w, _h)
		video_filters = []
		if _w == 480 and (_h == 368 or _h == 352): _h = 360
		#if STTNGS.has_key('s'):
		#	video_filters.append({'scale': '%d:%d'%(_w, _h)})

		print '\033[1;33m %dx%d  ==> %dx%d \033[00m'%(w,h, _w,_h)

		passes = [1,2]
		if STTNGS.has_key('passes'):
			passes = []
			for el in STTNGS['passes'].split(':'):
				passes.append(int(el))

		copyFlag = STTNGS['vcopy']
		if stream.params.has_key('extended'):
			if stream.params['extended'].has_key('copy'):
				copyFlag = copyFlag or stream.params['extended']['copy']

		if copyFlag:
			passes = [1]

		crf = 0
		if STTNGS.has_key('crf'):
			crf = STTNGS['crf']
		else:
			if stream.params.has_key('extended'):
				if stream.params['extended'].has_key('crf'):
					crf = stream.params['extended']['crf']
		if crf<>0:
			passes = [0]
		elif passes == [1]:
			passes = [None]

		hardsub_streams = []
		if stream.params.has_key('hardsub_streams'):
			hardsub_streams = stream.params['hardsub_streams']

		items2Delete = []
		for _pass in passes:
			ffmpeg_params = []
			if copyFlag:
				ffmpeg_params = self.__videoFfmpegParamsCopy(iFile, stream.trackID)
				ffmpeg_params.append('-an')
				#cmd = ffmpeg_path + ' -y -i "%s" -map %s -an -vcodec copy -threads %d'%(iFile, stream[1], STTNGS['threads'])
			else:
				lowQuality = _h<=320 or _w<=480
				ffmpeg_params = self.__videoFfmpegParamsQuality(iFile, stream.trackID, crf, _pass, not lowQuality)
				ffmpeg_params_add = ['-an']

				#if len(os_ffmpeg_prms):
				#	ffmpeg_params_add[len(ffmpeg_params_add):] = os_ffmpeg_prms
				if STTNGS.has_key('vr'):
					ffmpeg_params_add[len(ffmpeg_params_add):] = ['-r', '%.3f'%STTNGS['vr']]
					#cmd = '%s -r %.3f'%(cmd, STTNGS['vr'])

				# video filters section
				if len(hardsub_streams)==1:
					hardsub_stream = hardsub_streams[0]
					ass_fn = self.__prepareHardsubFile(hardsub_stream)
					if ass_fn!=None:
						#ffmpeg_params_add[len(ffmpeg_params_add):] = ['-vf', 'ass=%s'%ass_fn]
						video_filters.append({'ass': '%s'%add_separator_to_filepath(ass_fn)})
					else:
						print 'Can\'t set stream', hardsub_stream, 'as hardsub.'
						sys.exit(1)
						hardsub_stream.params['extended']['hardsub'] = False
				if STTNGS.has_key('crop'):
					#ffmpeg_params_add[len(ffmpeg_params_add):] = ['-vf', 'crop=%s'%STTNGS['crop']]
					video_filters.append({'crop': STTNGS['crop']})
				if STTNGS.has_key('s'):
					video_filters.append({'scale': '%d:%d'%(_w, _h)})
				if len(video_filters)>0:
					ffmpeg_params_add.append('-vf')
					filter_val = ''
					for filter_dict in video_filters:
						filter_name = filter_dict.keys()[0]
						filter_val += '%s=%s,'%(filter_name, filter_dict[filter_name])
					ffmpeg_params_add.append(filter_val[:-1])
				ffmpeg_params[len(ffmpeg_params):] = ffmpeg_params_add
			ffmpeg_params.append('"%s"'%oFile)

			if stream.params.has_key('extended') and stream.params['extended'].has_key('ffmpeg_coding_params'):
				ffmpeg_params = self.__mergeFfmpegParams(ffmpeg_params, stream.params['extended']['ffmpeg_coding_params'])

			#cmd = '%s "%s"'%(cmd, oFile)
			#cmd = ffmpeg_path + ' ' + ' '.join(ffmpeg_params)
			#self.__printCmd(cmd)
			if STTNGS['vc']:
				stream_prefix = None
				if stream.params.has_key('extended') and stream.params['extended'].has_key('stream_prefix'):
					stream_prefix = stream.params['extended']['stream_prefix']
				self.__exeFfmpegCmd(ffmpeg_params, stream_prefix)
				#p = os.popen(cmd)
				#p.close()

				if not copyFlag and len(passes)>1:
					d = 'pass%d'%_pass
					try:
						if not os.path.exists(d):
							os.makedirs(d)
						shutil.copyfile(oFile, '%s/%s'%(d, oFile))
						items2Delete.append('%s/%s'%(d, oFile))
						shutil.copyfile('x264_2pass.log', '%s/x264_2pass.log'%d)
						items2Delete.append('%s/x264_2pass.log'%d)
						items2Delete.append(d)
						#shutil.copyfile('ffmpeg2pass-0.log', '%s/ffmpeg2pass-0.log'%d)
						#shutil.copyfile('x264_2pass.log.temp', '%s/x264_2pass.log.temp'%d)
					except Exception, e:
						print e
		for itm in items2Delete:
			d = 'pass%d'%_pass
			try:
				if os.path.isdir(itm):
					os.rmdir(itm)
				else:
					os.remove(itm)
			except Exception, e:
				pass


	def __audioFfmpegParamsBase(self, fileName, _map):
		return ['-y', 
				'-i', '"'+fileName+'"',
				'-map', _map,
				'-vn']

	def __audioFfmpegParamsCopy(self, fileName, _map):
		rv = self.__audioFfmpegParamsBase(fileName, _map)
		rv[len(rv):] = ['-acodec', 'copy']
		return rv

	def __audioFfmpegParamsAac(self, fileName, _map, _ab, _ar):
		rv = self.__audioFfmpegParamsBase(fileName, _map)
		rv[len(rv):] = ['-acodec', 'aac', #'libfaac',
						'-ac', '2',
						'-ab', '%dk'%_ab,
						'-ar', '%d'%_ar]
		return rv

	def __audioFfmpegParamsTmpAc3(self, filename, _map, _ab, _ar, _threads):
		rv = self.__audioFfmpegParamsBase(filename, _map)
		rv[len(rv):] = ['-acodec', 'ac3',
						'-ac', '6',
						'-ab', '%dk'%_ab,
						'-ar', '%d'%_ar,
						'-threads', '%d'%_threads]
		return rv

	def cAudio(self, iFile, stream, oFile):
		add_params = ''
		ar = STTNGS['ar']
		ab = STTNGS['ab']
		copyFlag = False
		vol = 256
		if stream.params.has_key('extended'):
			if stream.params['extended'].has_key('ar'):
				ar = stream.params['extended']['ar']
			if stream.params['extended'].has_key('ab'):
				ab = stream.params['extended']['ab']
			if stream.params['extended'].has_key('vol'):
				vol = int(stream.params['extended']['vol'])
			if stream.params['extended'].has_key('copy'):
				copyFlag = stream.params['extended']['copy']
		else:
			copyFlag = STTNGS['acopy']
		if stream.params.has_key('frequency') and ar>stream.params['frequency']:
			ar = stream.params['frequency']
		if stream.params.has_key('bitrate') and ab>stream.params['bitrate']:
			ab = stream.params['bitrate']
		if stream.params.has_key('vol'):
			vol = int(stream.params['vol'])

		cmd = None
		ffmpeg_params = []
		ffmpeg_params_add = []
		if copyFlag or (stream.format().lower()=='aac' and stream.params.has_key('channels') and stream.params['channels']=='2' and stream.params.has_key('bitrate') and stream.params['bitrate']==ab and stream.params.has_key('frequency') and stream.params['frequency']==ar):
			#cmd = ffmpeg_path + ' -y -i "%s" -map %s -vn -acodec copy "%s"'%(iFile, stream[1], oFile)
			ffmpeg_params = self.__audioFfmpegParamsCopy(iFile, stream.trackID)
		else:
			#cmd = ffmpeg_path + ' -y -i "%s" -map %s -vn -acodec libfaac -ab %dk -ac 2 -ar %d -threads %d %s -strict experimental "%s"'%(iFile, stream[1], ab, ar, STTNGS['threads'], add_params, oFile)
			ffmpeg_params = self.__audioFfmpegParamsAac(iFile, stream.trackID, ab, ar)
			ffmpeg_params_add = ['-threads', '%d'%STTNGS['threads']]
			if vol!=256:
				ffmpeg_params_add[len(ffmpeg_params_add):] = ['-vol', '%d'%vol]
			ffmpeg_params[len(ffmpeg_params):] = ffmpeg_params_add
			ffmpeg_params_add = ffmpeg_params
			ffmpeg_params[len(ffmpeg_params):] = ['-strict', 'experimental']
		ffmpeg_params.append('"%s"'%oFile)

		if stream.params.has_key('extended') and stream.params['extended'].has_key('ffmpeg_coding_params'):
			ffmpeg_params = self.__mergeFfmpegParams(ffmpeg_params, stream.params['extended']['ffmpeg_coding_params'])

		#cmd = 'ffmpeg -y -i "%s" -map %s -vn -acodec copy -strict experimental "%s"'%(iFile, stream[1], oFile)
		#cmd = ffmpeg_path + ' ' + ' '.join(ffmpeg_params)
		#self.__printCmd(cmd)
		if STTNGS['ac']:
			stream_prefix = None
			if stream.params.has_key('extended') and stream.params['extended'].has_key('stream_prefix'):
				stream_prefix = stream.params['extended']['stream_prefix']
			#p = os.popen(cmd)
			#if p.close() is not None:
			if self.__exeFfmpegCmd(ffmpeg_params, stream_prefix)[0]<>0:
				#cmd = ffmpeg_path + ' -y -i "%s" -map %s -vn -acodec ac3 -ab 448k  -ar %d  -ac 6 -threads %d ./tmp.ac3'%(iFile, stream[1], ar, STTNGS['threads'])
				tmp_fn = '%s/tmp.ac3'%STTNGS['temp_dir']
				ffmpeg_params = self.__audioFfmpegParamsTmpAc3(iFile, stream.trackID, 448, ar, STTNGS['threads'])
				ffmpeg_params.append('"%s"'%tmp_fn)
				#cmd = ffmpeg_path + ' ' + ' '.join(ffmpeg_params)
				#self.__printCmd(cmd)
				#p = os.popen(cmd)
				#p.close()
				self.__exeFfmpegCmd(ffmpeg_params, stream_prefix)
					
				#cmd = ffmpeg_path + ' -y -i ./tmp.ac3 -vn -acodec libfaac -ab %dk  -ar %d  -ac 2 -threads %d %s "%s"'%(ab, ar, STTNGS['threads'], add_params, oFile)
				ffmpeg_params = ffmpeg_params_add
				try:
					idx = ffmpeg_params.index('-i')
				except Exception, e:
					raise e
				ffmpeg_params[idx+1] = '"%s"'%tmp_fn
				try:
					idx = ffmpeg_params.index('-map')
				except Exception, e:
					raise e
				del ffmpeg_params[idx:idx+2]
				ffmpeg_params.append('"%s"'%oFile)

				if stream.params.has_key('extended') and stream.params['extended'].has_key('ffmpeg_coding_params'):
					ffmpeg_params = self.__mergeFfmpegParams(ffmpeg_params, stream.params['extended']['ffmpeg_coding_params'])

				#cmd = ffmpeg_path + ' ' + ' '.join(ffmpeg_params)
				#self.__printCmd(cmd)
				#p = os.popen(cmd)
				#p.close()
				self.__exeFfmpegCmd(ffmpeg_params, stream_prefix)
					
				os.remove(tmp_fn)

	def cSubs(self, iFile, stream, informer, prms, oFile):
		if stream.params.has_key('extended') and stream.params['extended'].has_key('hardsub'):
			if stream.params['extended']['hardsub']:
				return None
			else:
				stream.params['extended']['hardsub'] = True
		ext = iFile.split('.')[-1].lower()
		if ext=='srt':
			if STTNGS['sc']:
				sConverter = subConverter(STTNGS)
				sConverter.srt2ttxt(iFile, oFile, prms)
		elif ext=='ass' or ext=='ssa':
			if STTNGS['sc']:
				sConverter = subConverter(STTNGS)
				sConverter.ass2ttxt(iFile, oFile, prms)
		elif ext=='ttxt':
			copyfile(iFile, oFile)
		elif ext=='mp4' or ext=='m4v':
			if stream.params.get('extended', {}).has_key('copy'):
				print 'subtitle from .mp4 files always copy'

			# TODO: extract or copy subtitles on ttxt format
			track_id = stream.params.get('mp4_track_id')
			if track_id is None:
				track_id = (int)(stream.trackID.split(self.mediainformer.mapStreamSeparatedSymbol(iFile))[1])+1

			fileName, fileExtension = os.path.splitext(iFile)
			tmpFile = oFile+fileExtension
			#shutil.copyfile(iFile, tmpFile)
			os.symlink(iFile, tmpFile)
			#cmd = mp4box_path + ' -raw %d \"%s\"'%(track_id, tmpFile) # or can use -single instead of -raw
			#cmd = mp4box_path + ' -single %d \"%s\"'%(track_id, tmpFile) # or can use -single instead of -raw
			#self.__printCmd(cmd)
			cmd = [mp4box_path, '-single', '%d'%track_id, tmpFile]
			self.__exeCmd(cmd)
			os.unlink(tmpFile)

			fileName, fileExtension = os.path.splitext(tmpFile)
			tmpFile = fileName + '_track%d'%track_id + fileExtension
			if not os.path.exists(tmpFile):
				tmpFile = fileName + '_track%d'%track_id
			return tmpFile
		else:
			if isMatroshkaMedia(iFile) and stream.params.has_key('mkvinfo_trackNumber'):
				if stream.format().upper()=='ASS' or stream.format().upper()=='SSA':
					assFileName = oFile+'.ass'
					#cmd = mkvtoolnix_path + 'mkvextract tracks "%s" %s:"%s"'%(iFile, stream.params['mkvinfo_trackNumber'], assFileName)
					#self.__printCmd(cmd)
					if STTNGS['sc']:
						#p = os.popen(cmd)
						#p.close()
						cmd = [mkvtoolnix_path + 'mkvextract', 'tracks', iFile, '%s:%s'%(stream.params['mkvinfo_trackNumber'], assFileName)]
						self.__exeCmd(cmd)
						sConverter = subConverter(STTNGS)
						sConverter.ass2ttxt(assFileName, oFile, prms)
						if STTNGS['ctf']:
							os.unlink(assFileName)
				else: # TODO: on mkv-files can be and other type's of subtitile
					strFileName = oFile+'.srt'
					#cmd = mkvtoolnix_path + 'mkvextract tracks "%s" %s:"%s"'%(iFile, stream.params['mkvinfo_trackNumber'], strFileName)
					#self.__printCmd(cmd)
					if STTNGS['sc']:
						#p = os.popen(cmd)
						#p.close()
						cmd = [mkvtoolnix_path + 'mkvextract', 'tracks', iFile, '%s:%s'%(stream.params['mkvinfo_trackNumber'], strFileName)]
						self.__exeCmd(cmd)
						sConverter = subConverter(STTNGS)
						sConverter.srt2ttxt(strFileName, oFile)
						if STTNGS['ctf']:
							os.unlink(strFileName)
			else:
				tmpName = iFile.split('/')[-1]+'_%s.srt'%stream.trackID
				#cmd = ffmpeg_path + ' -y -i "%s" -map %s -an -vn -sbsf mov2textsub -scodec copy "%s"'%(iFile, stream.trackID, tmpName)
				ffmpeg_params = ['-y',
								'-i', '"%s"'%iFile,
								'-map', stream.trackID,
								'-an',
								'-vn',
								'-sbsf', 'mov2textsub',
								'-scodec', 'copy',
								tmpName]
				#cmd = ffmpeg_path + ' ' + ' '.join(ffmpeg_params)
				#self.__printCmd(cmd)
				if STTNGS['sc']:
					stream_prefix = None
					if stream.params.has_key('extended') and stream.params['extended'].has_key('stream_prefix'):
						stream_prefix = stream.params['extended']['stream_prefix']
					self.__exeFfmpegCmd(ffmpeg_params, stream_prefix)
					#p = os.popen(cmd)
					#p.close()
					sConverter = subConverter(STTNGS)
					sConverter.ass2ttxt(tmpName, oFile)
					if STTNGS['ctf']:
						os.unlink(tmpName)
		return oFile

	def __streamById(self, streamId, streams):
		separator = self.mediainformer.mapStreamSeparatedSymbol()
		if str(streamId).isdigit():
			for s in streams:
				currStreamId = s.trackID.split(separator)[-1]
				if currStreamId==str(streamId):
					return s
		else:
			s = str(streamId).lower()
			stream_types_chars = 'vasi'
			tt = stream_types_chars.find(s[0])
			if tt > -1:
				s = s[1:]
				if len(s)>0 and s[0]=='_': s = s[1:]
			strm = None
			if s.isdigit():
				idx = int(s)
				tmp = filter(lambda a: a.type == tt, streams)
				if idx < len(tmp):
					strm = tmp[idx]
			elif len(s)>0:
				tmp = filter(lambda a: a.type==tt and a.language==s, streams)
				if len(tmp) > 0:
					strm = tmp[0]
			else:
				tmp = filter(lambda a: a.type==tt, streams)
				if len(tmp) > 0:
					strm = tmp[0]
			if strm <> None:
				return strm
		print 'Can\'t found stream #%s'%streamId
		sys.exit(1)
		return streams[streamId]

	def __streamFromFAdd(self, fadd, fi, currentTrack=0):
		path = os.path.dirname(fi.filename)
		if path[-1] != '/':
			path += '/'
		nn = self.buildFN(fi.filename, fadd[1])
		if not nn[0] in '/~':
			nn = path+nn
		#ext = nn.split('.')[-1].lower()
		if not os.path.exists(nn):
			print 'file "%s" not exist'%nn
			sys.exit(1)
		_fi = self.mediainformer.fileInfo(nn)
		_fi.streams[0].params['GlobalTrackNum'] = currentTrack
		name = None
		if fadd[-1].has_key('sname'):
			name = fadd[-1]['sname']

		# get stream info
		stream = None
		if fadd[2].has_key('stream'):
			#stream = _fi.streams[fadd[2]['stream']]
			stream = self.__streamById(fadd[2]['stream'], _fi.streams)
		else:
			for i in range(len(_fi.streams)):
				#tmp_stream = _fi.streams[i]
				tmp_stream = self.__streamById(i, _fi.streams)
				if tmp_stream.type==fadd[0]:
					stream = tmp_stream
					break
		if stream<>None:
			stream.params['extended'] = fadd[-1]
			stream.params['filename'] = _fi.filename
			stream.params['informer'] = _fi.informer
			stream.params['name'] = name
		return stream

	def splitMedia(self, filename):
		if STTNGS.has_key('ss'):
			print '------ Split Media ------'
			fi = self.mediainformer.fileInfo(filename)
			vstreams = filter(lambda s: s.type == 0, fi.streams)
			if len(vstreams):
				import uuid
				ext = filename.split('.')[-1].lower()
				#tmp_fn = str(uuid.uuid4())+'.'+ext
				tmp_fn = '.'.join(filename.split('.')[:-1])+'_tmp.'+ext
				os.rename(filename, tmp_fn)

				stream = vstreams[0]
				w = stream.params['width']
				h = stream.params['height']
				lowQuality = h<=320 or w<=480
				crf = STTNGS.get('crf', 16)
				ffmpeg_params = self.__videoFfmpegParamsQuality(tmp_fn, None, crf, 0, not lowQuality)
				ss_tmp = STTNGS['ss'].split('/')
				ss = ss_tmp[0]
				ffmpeg_params[len(ffmpeg_params):] = ['-acodec', 'copy', '-ss', ss]
				if len(ss_tmp)>1:
					ffmpeg_params.append('-t')
					ffmpeg_params.append(ss_tmp[1])
				ffmpeg_params.append(filename)
				self.__exeFfmpegCmd(ffmpeg_params)
				#os.unlink(tmp_fn)

	def createMPEGusingMP4Box(self, files, fi, name):
		addCmd2=''
		ve = ''
		ae = ''
		se = ''
		currentTrackIdx = 0
		trackID = 0
		if STTNGS['vv']:
			print
		info =  self.tagTrackInfo(os.path.basename(fi.filename))
		cmd = [mp4box_path, ]
		for f in files:
			def trackDelay(trackID):
				key = 'delay%d'%trackID	
				rv = 0		
				if STTNGS.has_key(key):
					rv = STTNGS[key]
				if STTNGS.has_key('episodes') and info.has_key('track') and type(info['track'])==type(1):
					eid = info['track']-1
					if STTNGS['episodes'][eid].has_key(key):
						rv = STTNGS['episodes'][eid][key]
				return rv

			stream = f[2]
			delay = 0
			if stream.params.has_key('extended'):
				if stream.params['extended'].has_key('delay'):
					delay = stream.params['extended']['delay']
			if delay==0:
				delay = trackDelay(trackID)

			if stream!=None:
				if stream.params.has_key('extended') and stream.params['extended'].has_key('lang'):
					(l, currentTrackIdx) = self.getLang(currentTrackIdx, stream.params['extended']['lang'])
					l = stream.params['extended']['lang'] 
				else:
					(l, currentTrackIdx) = self.getLang(currentTrackIdx, stream.language)
			else:
				(l, currentTrackIdx) = self.getLang(currentTrackIdx)
			addCmd2 = f[1]
			if l <> 'und':
				addCmd2 += ':lang=%s'%l
			#addCmd2 += ' -add "%s":lang=%s'%(string.replace(f[1], '0.0', '0:0'), l,)
			if delay!=0:
				addCmd2 += ':delay=%d'%delay
			if f[0]>0:
				addCmd2 += ':group=%d'%f[0]
			if stream.params.has_key('name') and stream.params['name']<>None:
				addCmd2+=':name=%s'%stream.params['name']
			if f[0]==0:
				addCmd2 += ve
				ve = ':disable'
			elif f[0]==1:
				addCmd2 += ae
				ae = ':disable'
			elif f[0]==2:
				addCmd2 += se
				se = ':disable'
			trackID+=1
			cmd.append('-add')
			cmd.append(addCmd2)

		cmd.append(name)
		cmd.append('-new')
		#cmd = mp4box_path + ' %s "%s" -new'%(addCmd2, name)
		#self.__printCmd(cmd)
		#p = os.popen(cmd)
		#p.close()
		rv = self.__exeCmd(cmd, False)
		return rv

	def createMPEGusingFfmpeg(self, files, fi, name):
		addCmd2=''
		currentTrackIdx = 0
		trackID = 0
		if STTNGS['vv']:
			print
		info =  self.tagTrackInfo(os.path.basename(fi.filename))
		cmd = [ffmpeg_path, '-y', ]
		for f in files:
			stream = f[2]
			addCmd2 = f[1]
			cmd.append('-i')
			cmd.append(addCmd2)

		cmd[len(cmd):] = ['-c:v', 'copy', '-c:a', 'copy', '-bsf:a', 'aac_adtstoasc', '-strict', 'experimental']
		cmd.append(name)
		#cmd = mp4box_path + ' %s "%s" -new'%(addCmd2, name)
		#self.__printCmd(cmd)
		#p = os.popen(cmd)
		#p.close()
		rv = self.__exeCmd(cmd, False)
		return rv

	def createMPEG(self, files, fi):
		name = STTNGS['temp_dir']+'/'+'.'.join(os.path.basename(fi.filename).split('.')[:-1])+'.'+STTNGS['format']
		ret_code = self.createMPEGusingMP4Box(files, fi, name)

		if ret_code <> 0:
			rv = self.createMPEGusingFfmpeg(files, fi, name)
			if rv <> 0:
				print 'Merge streams failed, code:', rv
				sys.exit(rv)

		self.iTagger(name)
		
		self.log.put('Fixing flags on result mpeg file...\n')
		if not STTNGS.get('test_mode'):
			mpeg4fixer().fixFlagsAndSubs(name, STTNGS['fd'])
		
		'''
		self.log.put('Setting stream names...\n')
		trackNames = []
		need = False
		for f in files:
			n = None
			if f[2]!=None and f[2].params.has_key('name') and f[2].params['name']:
				n = unicode(f[2].params['name'], 'utf-8').encode('utf-8')
				need = True
			trackNames.append(n)
		if need:
			mpeg4fixer().setTrackNames(name, trackNames) 
		'''
		return name

	def createMKV(self, files, fi):
		name = STTNGS['temp_dir']+'/'+'.'.join(os.path.basename(fi.filename).split('.')[:-1])+'.'+STTNGS['format']
		cmd = [mkvtoolnix_path + 'mkvmerge', '-o', name, ]
		for f in files:
			cmd.append(f[1])
		retcode = self.__exeCmd(cmd, False)
		if retcode>1:
			print cmd
			print 'Exit with code: %d'%retcode
			sys.exit()
		return name


	def encodeMedia(self, fi):
		'''
			convert media
		'''
		name = os.path.basename(fi.filename)
		files = []
		addCmd = ''
		findSubs = True	
		(ve, ae, se) = ('', '', '')
		tmp = STTNGS['streams']
		strms = []
		if tmp=='' or tmp=='all':
			for i in range(len(fi.streams)):
				strms.append(i)
		elif tmp=='none':
			pass
		else:
			for s in tmp.split(':'):
				strms.append(s)


		# check hardsub and get unique media file names for logging
		hardsub_streams = []
		media_file_names = set()
		for i in strms:
			stream = self.__streamById(i, fi.streams)
			if stream.params.has_key('extended') and stream.params['extended'].has_key('hardsub'):
				stream.params['filename'] = fi.filename
				hardsub_stream.append(stream)
			media_file_names.add(fi.filename)
		for fadd in STTNGS['fadd']:
			stream = self.__streamFromFAdd(fadd, fi)
			if stream.params.has_key('extended') and stream.params['extended'].has_key('hardsub'):
				hardsub_streams.append(stream)
			media_file_names.add(stream.params['filename'])
		for x in media_file_names:
			self.log.put('----------------------------\n', False)
			self.log.put(self.mediainformer.fileInfo(x).dump(), True)
		self.log.put('----------------------------\n', False)

		sConverter = subConverter(STTNGS)
		currentTrack = 0
		out_fn = '%s/%s'%(STTNGS['temp_dir'], name)
		for i in strms:
			#stream = fi.streams[i]
			stream = self.__streamById(i, fi.streams)
			stream.params['GlobalTrackNum'] = currentTrack
			if STTNGS['vv']:
				print stream

			if stream.type==0:
				if len(hardsub_streams)>0:
					stream.params['hardsub_streams'] = hardsub_streams
					hardsub_streams = []
				files.append((0, out_fn+'_%s.mp4'%stream.trackID, stream))
				self.cVideo(fi.filename, stream, files[-1][1])

			elif stream.type==1:
				files.append((1, out_fn+'_%s.aac'%stream.trackID, stream))
				self.cAudio(fi.filename, stream, files[-1][1])

			elif stream.type==2:
				ttxtName = out_fn+'_%s.ttxt'%stream.trackID
				tmpFile = self.cSubs(fi.filename, stream, fi.informer, {}, ttxtName)
				if tmpFile<>None:
					files.append((2, tmpFile, stream))
					findSubs = False
			if STTNGS['vv']:
				print '----------------------------------------', currentTrack
			currentTrack+=1
	
		# add external streams
		path = os.path.dirname(fi.filename)+'/'
		for add in STTNGS['fadd']:
			stream = self.__streamFromFAdd(add, fi, currentTrack)
			if stream==None:
				print "Can't find stream (type: %d) in file %s or incorrect number"%(add[0], nn)
				sys.exit(1)

			out_fn = '%s/%s_%s'%(STTNGS['temp_dir'], os.path.basename(stream.params['filename']), stream.trackID)
			if stream.params['name']<>None and stream.params['name']!='':
				if len(stream.params['name']):
					out_fn = '%s_%s'%(out_fn, stream.params['name'])

			print add
			if add[0]==0:
				out_fn = out_fn + '.mp4'
				if len(hardsub_streams)>0:
					stream.params['hardsub_streams'] = hardsub_streams
					hardsub_streams = []
				files.append((0, out_fn, stream))
				self.cVideo(stream.params['filename'], stream, files[-1][1])

			elif add[0]==1:
				out_fn = out_fn + '.aac'
				files.append((1, out_fn, stream))
				self.cAudio(stream.params['filename'], stream, files[-1][1])

			elif add[0]==2:
				out_fn = out_fn + '.ttxt'
				#files.append((2, out_fn, stream))
				tmpFile = self.cSubs(stream.params['filename'], stream, stream.params['informer'], add[2], out_fn)
				if tmpFile<>None:
					files.append((2, tmpFile, stream))
					findSubs = False

			if STTNGS['vv']:
				print '----------------------------------------', currentTrack
			currentTrack+=1

		'''
		# try to find subtitles in external file's
		nm = '.'.join(os.path.basename(fi['filename']).split('.')[:-1])
		if findSubs:
			if os.path.exists('%s%s.srt'%(path,nm)):
				files.append((2,'./%s.srt'%nm, None))
				if STTNGS['sc']:
					sConverter.srt2ttxt('%s%s.srt'%(path,nm), files[-1][1])
			if os.path.exists('%s%s.ass'%(path,nm)):
				files.append((2,'%s.ttxt'%nm, None))
				if STTNGS['sc']:
					sConverter.ass2ttxt('%s%s.ass'%(path,nm), files[-1][1])
			if os.path.exists('%s%s.ssa'%(path,nm)):
				files.append((2,'%s.ttxt'%nm, None))
				if STTNGS['sc']:
					sConverter.ass2ttxt('%s%s.ssa'%(path,nm), files[-1][1])
		'''
	
			
		#print 'files: ',files
		if STTNGS['vv']:
			print

		# write streams to output file
		format = STTNGS['format'].lower()
		if format in ['m4v', 'mp4', 'mov']:
			name = self.createMPEG(files, fi)
		elif format in ['mkv']:
			STTNGS['web_optimization'] = False
			name = self.createMKV(files, fi)

		self.splitMedia(name)

		self.log.put('Remove temp files...\n')
		if STTNGS['ctf']:
			for f in files:
				try:
					os.unlink(f[1])
				except OSError as e:
					print('Can\'t remove file: %s'%f[1])
				

		return name


	def fileProcessing(self, fi):
		'''
			Processing one media file
		'''
		filename = fi.filename
		if STTNGS.has_key('tagging_mode'):
			self.splitMedia(filename)
			self.iTagger(filename)
		else:
			filename = self.encodeMedia(fi)

		if STTNGS['web_optimization']:
			cmd = [mp4box_path, '-inter', '500', filename]
			self.__exeCmd(cmd)

		self.rename(filename)


	def correct_profile(self, video, **kwargs):
		if kwargs.get('dry_run', False):
			print " ".join([sq(x) for x in (kwargs['argv0'], '--correct-profile-only', video)])
		else:
			level_string = struct.pack('b', int('29', 16))
			fobj = open(video, 'r+b')
			try:
				fobj.seek(7)
				print 1, 'correcting profile:', video
				fobj.write(level_string)
			finally:
				fobj.close()




if __name__=='__main__':
	script_path = os.path.dirname(os.path.realpath(__file__))
	# set 'FONTCONFIG_FILE' environment variable for font_config
	if os.environ.get('FONTCONFIG_FILE') is None:
		os.environ['FONTCONFIG_FILE'] = '%s/fonts.conf'%script_path

	converter = Video2iDevice()

	startTime = time.time()
	argv = sys.argv[1:]
	JSON_pipe = len(argv)==1 and argv[0]=='-json_pipe'
	if len(sys.argv)==1 or JSON_pipe:
		i, o, e = select.select([sys.stdin], [], [], 3)
		if i:
			if JSON_pipe:
				argv = json_ex.JsonReader().read(sys.stdin.read())
			else:
				argv = shlex.split(sys.stdin.read())
		else:
			argv = ['-h']
	yep = False
	for el in argv:
		if yep:
			STTNGS['tfile'] = el
			break
		if el=='-tfile':
			yep = True
	if len(STTNGS['tfile'])>0:
		TAGS = converter.loadSettingsFile(STTNGS['tfile'])
		for key,val in TAGS.items():
			#if type(val)==type(''):
			#	val = unicode(val, 'utf-8')
			if key=='TRACK_REGEX' or key=='TRACKS_REGEX':
				if not STTNGS.has_key(key):
					STTNGS[key] = val.split(';')
			else:
				if not STTNGS.has_key(key):
					STTNGS[key] = val
	#print STTNGS['subStyleColors']
	converter.getSettings(argv)

	if STTNGS.has_key('out_path'):
		os.chdir(STTNGS['out_path'])

	if STTNGS.has_key('log_file'):
		converter.log.initLogByFileName(STTNGS['log_file'])
	converter.log.put('argv: %s\n'%argv.__str__(), True)

	if not STTNGS.has_key('threads'):
		STTNGS['threads'] = os.sysconf('SC_NPROCESSORS_CONF')
	if converter.log.isSetted():
		import platform
		converter.log.put('Version: %s\n'%STTNGS['version'], False)
		converter.log.put('Platform: %s\n'%platform.uname().__str__(), False)
		converter.log.put('Threads: %d\n\n'%STTNGS['threads'], True)

	if STTNGS['temp_dir'][-1]=='/':
		STTNGS['temp_dir'] = STTNGS['temp_dir'][:-1]
	if not os.path.exists(STTNGS['temp_dir']):
		print os.mkdir(STTNGS['temp_dir'])


	converter.mediainformer.artwork_path = STTNGS['temp_dir']

	c = 0
	for fn in STTNGS['files']:
		if STTNGS['vv']:
			print '\n------------------------ %s ------------------------'%fn
		if STTNGS.has_key('info'):
			fi = converter.mediainformer.fileInfo(fn)
			#fi.streams = map(lambda x: [x.type, x.trackID[x.trackID.index(converter.mediainformer.mapStreamSeparatedSymbol(fi.filename))+1:], x.language, x.params], fi.streams)
			#print type(fi['streams'][2][1])
			#sys.exit()
			if STTNGS['info']=='json':
				print json_ex.write(fi.dump('dict'))
			elif STTNGS['info']=='short':
				print fi.dump('short')
			else:
				print fi.dump()
		else:
			if STTNGS['sleep_between_files'] > 0 and c > 0:
				print 'Sleeping...'
				time.sleep(STTNGS['sleep_between_files'])
			if STTNGS['streams']=='none':
				#fi = {'filename': fn, 'informer': 'no need'}
				fi = cMediaInfo('no need', fn)
			else:
				fi = converter.mediainformer.fileInfo(fn)
			converter.fileProcessing(fi)
		c += 1
	tm = time.time()-startTime
	time_str = '%02d:%02d:%.3f'%(tm/60/60, tm%(60*60)/60, int(tm%60)+(tm-int(tm)))
	if not (STTNGS.has_key('info') and not STTNGS['vv']):
		print 'time %s'%time_str

	converter.log.put('time %s\n'%time_str, True)

	if converter.log.isSetted():
		try:
			from constants import SERVICE_XMPP_UID, SERVICE_XMPP_PASS, XMPP_UID
			send_xmpp_message(SERVICE_XMPP_UID, SERVICE_XMPP_PASS, XMPP_UID, 'Convertion "%s" complite.'%'.'.join(os.path.basename(converter.log.file_name()).split('.')[:-1]))
		except:
			pass


	converter.log.releaseLog()

