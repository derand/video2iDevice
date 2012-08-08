#!/usr/bin/env python
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


#####################  #########################

import sys
import os
import re
import getopt
import glob
import string
import json
import os.path
import time
import shutil
import fileCoding
import os.path

import xml.parsers.expat
from subprocess import Popen, PIPE

from subConverter import subConverter
from mpeg4fixer import mpeg4fixer

import select
import shlex

from mediaInfo import cStream, cMediaInfo, cChapter, MediaInformer, add_separator_to_filepath, isMatroshkaMedia


STTNGS = {
	'version' : '0.5.4',
#	'threads':	3,
	'files':	[],
	'mn':		False,
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
	'vq':		3,
	'format':	'm4v',
	'add2TrackIdx': 0,
	'vcopy':	False,
	'acopy':	False,
	'vr':		23.976,
	'ctf':		False,
	'rn':		False,
	'vv':		False,
	'web_optimization': False,
	'temp_dir': '.',
	'encodingTool': '2iDevice.py (http://blog.derand.net)',
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

Options
	-h			this help
	-th		[int]	using threads for coding
	-lang		[str]	languages of srteams separated ':' (also can set for each track like 'stream' param)
	-cn			disable converting step, merge streams files to .m4v file
	-vn			disable convert video
	-an			disable convert audio
	-sn			disable convert subtitles
	-ar		[int]	audio frequency (def 48000)
	-ab		[int]	audio bitrate (def 128k)
	-b		[int]	video bitrate (def 960)
	-crf 		[int]	one pass coding, crf param
	-refs		[int]	ref frames for coding video
	-tn			disable sets tags
	-mn			disable merge
	-streams	[str]	select streams numbers or 'none' for none (first index 0 separated ':', default 'all')
	-tfile		[str]	set tags file
	-track		[int]	track
	-tracks		[int]	tracks count
	-sfile		[str]	set subtitle filename. If not set try search in current dir. 
				Can be format:
					[NAME] - origin name of file
					[2EID] - episode id (evaluate from regext in tfile)
					[2EC] - episode count
	-out_file	[str]	save result to this file. supports tags: [SEASON], [EPISODE_ID]
	-fd			fix video duration
	-et		[str]	set episodes titles separated ';'
	-stik		[str]	set iTunes stick. can be 'Movie', 'Music Video', 'TV Show' ... (see: AtomicParsley --stik-list)
	-TVShowName	[str]	set showname tag
	-TVSeasonNum	[str]	set season num
	-description	[str]	set deascription
	-year		[str]	set year
	-artwork	[str]	set artwork filename
	-movie_name	[srt]	set movie name
	-TRACK_REGEX	[srt]	set regular exeption for select track from filename
	-TRACKS_REGEX	[srt]	set regular exeption for select tracks from filename
	-vq		[int]	(deprecated: use -s) video quality (1 - 480x*,   2 - *x320, 3 - max)
	-format		[str]	output format (default: 'm4v')
	-stream		[int]	stream idx from appending files (vfile, afile, sfile)
	-title		[srt]	stream title from appending files (vfile, afile, sfile)
	-add2TrackIdx	[int]	add to track (def: 0)
	-s		[int]x[int]	result resolution, can looks like ('*x320', '960x*')
	-v			script version
	-passes  	[str]	video passes coding separeted ':'
	-vr        	[float]	frame rate (default 23.976)
	-addTimeDiff 	[int]	add time(ms) diff to subs (last sub stream)
	-vcopy			(deprecated: use -copy) copy video stream
	-acopy			(deprecated: use -copy) copy audio stream
	-copy			copy selected stream	
	-avol		[int]	change audio volume (def 256=100%), only for 'afile' params
	-ctf			clear temp files after converting
	-rn			don't resize video
	-crop	[int]:[int]:[int]:[int]	crop video (width:height:x:y)
	-delay		[int]	sets track start delay in ms.
	-info 			show media file info
	-vv			verbose mode
	-temp_dir	[str]	path to temporary directory
	-hardsub		set stream as hurdsub (for ass format only)
	-ffmpeg_coding_params	[str]	add ffmpeg params for video/audio coding (set's for selected stream)
	-json_pipe		set all params by JSON array [] in pipe, this should be only param on parameters
	-web_optimization	optimization result file to streaming
	-tagging_mode		set tags only

For tagging you can use AtomicParsley long-option params (see "AtomicParsley -h"), in param use one '-' symbol like:
	./2iDevice.py <filename> -contentRating Unrated
for AtomicParsley --contentRating Unrated.
	
Author
	Writen by Andrey Derevyagin (2derand+2idevice@gmail.com)

Copyright
	Copyright © 2010-2012 Andrey Derevyagin
  
Bugs
	If you feel you have found a bug in "2iDevice", please email me 2derand+2idevice@gmail.com
'''

#black_list = ('EdKara', 'TVLpaint', 'SerialMainTitle', 'Kar_OP_1', 'Kar_OP_2', 'Kar_OP_3', 'Kar_OP_4', 'Kar_ED_1', 'Kar_ED_2', 'Kar_ED_3', 'Kar_ED_4', 'Kar_ED_5', 'Kar_ED_6' )


if sys.platform == 'darwin':
	script_dir = add_separator_to_filepath(os.path.dirname(os.path.realpath(__file__)))
	ffmpeg_path = script_dir + '/binary/ffmpeg'
	mp4box_path = script_dir + '/binary/MP4Box'
	AtomicParsley_path = script_dir + '/binary/AtomicParsley'
	mkvtoolnix_path = script_dir + '/binary/mkvtoolnix/'
	mediainfo_path = script_dir + '/binary/mediainfo'

	os_ffmpeg_prms = []
else:
	ffmpeg_path = 'ffmpeg'
	mp4box_path = 'MP4Box'
	AtomicParsley_path = 'AtomicParsley'
	mkvtoolnix_path = ''
	mediainfo_path = 'mediainfo'

	os_ffmpeg_prms = ['-flags2', '+bpyramid-mixed_refs+wpred+dct8x8+fastpskip']





class Video2iDevice(object):
	"""docstring for Video2iDevice"""
	def __init__(self):
		super(Video2iDevice, self).__init__()
		self.mediainformer = MediaInformer(ffmpeg_path, mkvtoolnix_path, mediainfo_path, AtomicParsley_path, STTNGS['temp_dir'])

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
				if ckey=='rn':
					STTNGS['rn'] = True
					saveP = True
				if ckey=='vcopy':
					STTNGS['vcopy'] = True
					saveP = True
				if ckey=='acopy':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1]['copy'] = True
					else:
						STTNGS['acopy'] = True
					saveP = True
				if ckey=='copy':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1]['copy'] = True
				if ckey=='tn' or ckey=='mn':
					STTNGS[ckey] = True
					saveP = True
				if ckey=='fd':
					STTNGS['fd'] = True
					saveP = True
				elif ckey=='ctf':
					STTNGS['ctf']=True
					saveP = True
				if ckey=='addTimeDiff':
					waitParam = True
				if ckey=='add2TrackIdx':
					waitParam = True
				if ckey=='info' or ckey=='vv' or ckey=='web_optimization' or ckey=='tagging_mode':
					STTNGS[ckey] = True
					saveP = True
				if ckey=='h' or ckey=='json_pipe':
					print help
					sys.exit(0)
				if ckey=='v':
					print "Version: %s"%STTNGS['version']
					sys.exit(0)
				elif ckey=='hardsub':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1][ckey] = True
					saveP = True
				elif ckey=='ffmpeg_coding_params':
					waitParam = True
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
						tmp[-1][-1]['stream'] = int(el)
				elif ckey=='title':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1]['title'] = el
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
						tmp[-1][-1]['crf'] = int(el)
					else:
						STTNGS[ckey] = int(el)
				elif ckey=='ffmpeg_coding_params':
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						tmp[-1][-1][ckey] = shlex.split(el)
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
			file = open(filename, 'r')
		except:
			print 'error open file %s'%filename
			sys.exit(1)
		inside_key = False
		save_key = ''
		_tmp = ''
		rv = {}
		arrSymb = None
		for line in file:
			if len(line)==1 or line[0]=='#':
				continue
			if inside_key:
				_tmp += line.strip()
				if _tmp[-1]==arrSymb:
					if inside_key:
						if STTNGS['vv']:
							print _tmp
						#rv[save_key] = json.loads(_tmp)
						rv[save_key] = json.JsonReader().read(_tmp)
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
						rv[key] = json.JsonReader().read(val)
					else:
						save_key  =key
						_tmp = val
						inside_key = True
				else:
					rv[key] = val
		return rv
		
	def __printCmd(self, cmd):
		print ': \033[1;32m%s\033[00m'%cmd

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
		if STTNGS.has_key('artwork'):
			rv['artwork'] = STTNGS['artwork']
		if STTNGS.has_key('stik'):
			rv['stik'] = STTNGS['stik']
		if STTNGS.has_key('TVShowName'):
			rv['show'] = STTNGS['TVShowName']
		if STTNGS.has_key('TVSeasonNum'):
			rv['season'] = STTNGS['TVSeasonNum']
		if STTNGS.has_key('description'):
			rv['description'] = STTNGS['description']
		if STTNGS.has_key('year'):
			rv['year'] = STTNGS['year']
		if STTNGS.has_key('artist'):
			rv['artist'] = STTNGS['artist']
		if STTNGS.has_key('movie_name'):
			rv['movie_name'] = STTNGS['movie_name']
		if tr==None and not rv.has_key('season'):
			srch = re.compile('[sS](\d{2})[eE](\d{2})').search(fn)
			if srch!=None:
				tr = int(srch.groups()[1])+STTNGS['add2TrackIdx']
				rv['track'] = tr
				rv['season'] = int(srch.groups()[0])
		return rv

	def iTagger(self, fn):
		def __add_param(info, name, _id, prms):
			if info.has_key(_id):
				return prms + ' %s "%s"'%(name, info[_id])
			return prms

		if not STTNGS['tn']:
			#prms = ' --copyright "derand"'
			prms = {
				'encodingTool': STTNGS['encodingTool'],
				#'overWrite': ''
			}
			info = self.tagTrackInfo(fn)
			'''
			prms = __add_param(info, '--artwork', 'artwork', prms)
			prms = __add_param(info, '--stik', 'stik', prms)
			prms = __add_param(info, '--TVShowName', 'show', prms)
			prms = __add_param(info, '--album', 'show', prms)
			prms = __add_param(info, '--artist', 'show', prms)
			prms = __add_param(info, '--TVSeasonNum', 'season', prms)
			prms = __add_param(info, '--description', 'description', prms)
			prms = __add_param(info, '--year', 'year', prms)
			if prms.find(' --artist ')==-1:
				prms = __add_param(info, '--artist', 'artist', prms)
			prms = __add_param(info, '--title', 'movie_name', prms)
			'''
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
					title = '"%s"'%STTNGS['episodes_titles'][track-1].replace("`", '_')
					#prms += ' --TVEpisode %s'%title
					#prms += ' --title %s'%title
					prms['TVEpisode'] = title
					prms['title'] = title
				elif STTNGS.has_key('episodes') and len(STTNGS['episodes'])>(track-1):
					epInfo = STTNGS['episodes'][track-1]
					for option in atomicParsleyOptions:
						if epInfo.has_key(option):
							if option=='title':
								prms['TVEpisode'] = ' "%s"'%epInfo[option]
							prms[option] = ' "%s"'%epInfo[option]
				else:
					#prms += ' --TVEpisode "%s"'%fn
					title = os.path.basename(fn)
					title = os.path.splitext(title)[0]
					prms['TVEpisode'] = '"%s"'%title

			#prms += ' --encodingTool "2iDevice.py (http://blog.derand.net)" --overWrite'
			prms_str = ''
			for p in prms.keys():
				if prms[p].find(' ')==-1 or (prms[p][0]=='\"' and prms[p][-1]=='\"' and prms[p].count('\"')==2):
					prms_str += ' --%s %s'%(p, prms[p])
				else:
					prms_str += ' --%s "%s"'%(p, prms[p])
			cmd = AtomicParsley_path + ' "%s" %s --overWrite'%(unicode(fn,'UTF-8'), unicode(prms_str, 'UTF-8'))
			self.__printCmd(cmd.encode('utf-8'))
			os.system(cmd.encode('utf-8'))

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
		cmd = 'mv "%s" "%s"'%(fn, name)
		self.__printCmd(cmd)
		os.system(cmd)

	def sizeConvert(self, real1, real2, out1):
		out2 = (real2*out1)/real1
		if out2%16>7:
			out2 += 16-out2%16
		else:
			out2 -= out2%16
		return (out1, out2)

	def __videoFfmpegParamsBase(self, fileName, _map):
		return ['-y', 
				'-i', '"'+fileName+'"',
				'-map', _map,
				'-an']

	def __videoFfmpegParamsCopy(self, fileName, _map):
		rv = self.__videoFfmpegParamsBase(fileName, _map)
		rv[len(rv):] = ['-vcodec', 'copy']
		return rv

	def __videoFfmpegParamsPasses(self, fileName, _map, _pass):
		rv = self.__videoFfmpegParamsBase(fileName, _map)
		add = ['-pass', '%s'%_pass,
				'-vcodec', 'libx264',
				'-flags', '+loop',
				'-cmp','+chroma',
				'-me_method','full']
		rv[len(rv):] = add
		return rv

	def __videoFfmpegParamsCRF(self, fileName, _map, crf):
		rv = self.__videoFfmpegParamsBase(fileName, _map)
		add = ['-vcodec', 'libx264',
			   '-crf', '%d'%crf]
		rv[len(rv):] = add
		return rv

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
				if idx==-1:
					current_params.insert(-1, param)
					if val!=None:
						current_params.insert(-1, val)
				else:
					if val!=None:
						current_params[idx+1] = val
		return current_params


	def __prepareHardsubFile(self, hardsub_stream):
		fn = hardsub_stream.params['filename']
		_, file_ext = os.path.splitext(fn)
		file_ext = file_ext.lower()
		if file_ext=='.ass' or file_ext=='.ssa':
			ass_fn = '%s/%s'%(STTNGS['temp_dir'], os.path.basename(fn))
			shutil.copyfile(fn, ass_fn)
		elif isMatroshkaMedia(fn) and hardsub_stream.params.has_key('mkvinfo_trackNumber'):
			if hardsub_stream.format().upper()=='ASS' or hardsub_stream.format().upper()=='SSA':
				ass_fn = '%s/%s.ass'%(STTNGS['temp_dir'], os.path.basename(fn), hardsub_stream.format().lower())
				cmd = mkvtoolnix_path + 'mkvextract tracks "%s" %s:"%s"'%(fn, hardsub_stream.params['mkvinfo_trackNumber'], ass_fn)
				self.__printCmd(cmd)
				p = os.popen(cmd)
				p.close()
		else:
			# TODO: there can be added other subtitle format
			return None

		ass_fn = add_separator_to_filepath(ass_fn)
		return ass_fn


	def cVideo(self, iFile, stream, oFile):
		print stream.params
		w = stream.params['width']
		h = stream.params['height']
		if stream.params.has_key('dwidth') and stream.params.has_key('dheight'):
			w = stream.params['dwidth']
			h = stream.params['dheight']
	
		if not STTNGS['rn']:
			if STTNGS.has_key('s'):
				res = STTNGS['s'].split('x')
				if res[0]=='*':
					(_h, _w) = self.sizeConvert(h, w, int(res[1]))
				elif res[1]=='*':
					(_w, _h) = self.sizeConvert(w, h, int(res[0]))
				else:
					_w = int(res[0])
					_h = int(res[1])
			else:
				(_w, _h) = (w, h)
				#(_w, _h) = self.sizeConvert(w, h, w)
				#(_h, _w) = self.sizeConvert(_h, _w, _h)
				'''
				if STTNGS['vq']==1:
					(_w, _h) = self.sizeConvert(w, h, 480)
				elif STTNGS['vq']==2:
					(_h, _w) = self.sizeConvert(h, w, 320)
				else:
					(_w, _h) = self.sizeConvert(w, h, 480)
					if _h<320:
						(_h, _w) = self.sizeConvert(h, w, 320)
				'''
		else:
			(_w, _h) = (w, h)
		if _w == 480 and (_h == 368 or _h == 352): _h = 360

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
					crf = int(stream.params['extended']['crf'])
		if crf<>0:
			passes = [0]

		hardsub_streams = []
		if stream.params.has_key('hardsub_streams'):
			hardsub_streams = stream.params['hardsub_streams']

	
		items2Delete = []
		for _pass in passes:
			ffmpeg_params = []
			if copyFlag:
				ffmpeg_params = self.__videoFfmpegParamsCopy(iFile, stream.trackID)
				#cmd = ffmpeg_path + ' -y -i "%s" -map %s -an -vcodec copy -threads %d'%(iFile, stream[1], STTNGS['threads'])
			else:
				ffmpeg_params = []
				ffmpeg_params_add = []
				if  crf<>0:
					'CRF mode'
					ffmpeg_params = self.__videoFfmpegParamsCRF(iFile, stream.trackID, crf)
					ffmpeg_params_add = ['-s', '"%dx%d"'%(_w,_h),
										 '-refs', '%d'%STTNGS['refs'],
										 '-threads', '%d'%STTNGS['threads']]
				else:
					'PASSES mode'
					ffmpeg_params = self.__videoFfmpegParamsPasses(iFile, stream.trackID, _pass)
					ffmpeg_params_add = ['-b:v', '"%d k"'%STTNGS['b'],
										 '-s', '"%dx%d"'%(_w,_h),
										 '-maxrate', '"%d k"'%STTNGS['b'],
										 '-bufsize', '"%d k"'%int(STTNGS['b']*2.5),
										 '-refs', '%d'%STTNGS['refs'],
										 '-threads', '%d'%STTNGS['threads']]
					ffmpeg_params_add[len(ffmpeg_params_add):] = os_ffmpeg_prms
				ffmpeg_params[len(ffmpeg_params):] = ffmpeg_params_add
				ffmpeg_params_add = []
				if _h<=320 or _w<=480:
					''' LOW QUALITY '''
					ffmpeg_params_add = ['-partitions', '+parti4x4+partp8x8+partb8x8',
										 '-subq', '6',
										 '-trellis','0',
										 '-coder', '0',
										 '-me_range', '16',
										 '-level', '3.1',
										 '-profile:v', 'baseline']
					#cmd = ffmpeg_path + ' -y -i "%s" -pass %d -map %s -an  -vcodec "libx264" -b:v "%d k" -s "%dx%d" -flags "+loop" -cmp "+chroma" -partitions "+parti4x4+partp8x8+partb8x8" -subq 6  -trellis 0  -refs %d  -coder 0  -me_range 16  -g 240   -keyint_min 25  -sc_threshold 40 -i_qfactor 0.71 -maxrate  "%d k" -bufsize "%d k" -rc_eq "blurCplx^(1-qComp)" -qcomp 0.6 -me_method full -b_strategy 1 %s -level 3.1 -threads %d -profile baseline '%(iFile, _pass, stream[1], STTNGS['b'], _w,_h, STTNGS['refs'], STTNGS['b'], STTNGS['b']*2.5, os_ffmpeg_prms, STTNGS['threads'])
				else:
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
				#if len(os_ffmpeg_prms):
				#	ffmpeg_params_add[len(ffmpeg_params_add):] = os_ffmpeg_prms
				if len(hardsub_streams)==1:
					hardsub_stream = hardsub_streams[0]
					print hardsub_stream
					ass_fn = self.__prepareHardsubFile(hardsub_stream)
					if ass_fn!=None:
						ffmpeg_params_add[len(ffmpeg_params_add):] = ['-vf', 'ass="%s"'%ass_fn]
					else:
						print 'Can\'t set stream', hardsub_stream, 'as hardsub.'
						sys.exit(1)
						hardsub_stream.params['extended']['hardsub'] = False
				if STTNGS.has_key('vr'):
					ffmpeg_params_add[len(ffmpeg_params_add):] = ['-r', '%.3f'%STTNGS['vr']]
					#cmd = '%s -r %.3f'%(cmd, STTNGS['vr'])
				if STTNGS.has_key('crop'):
					ffmpeg_params_add[len(ffmpeg_params_add):] = ['-vf', 'crop=%s'%STTNGS['crop']]
					#cmd = '%s -vf crop=%s'%(cmd, STTNGS['crop'])
				ffmpeg_params[len(ffmpeg_params):] = ffmpeg_params_add
			ffmpeg_params.append('"%s"'%oFile)

			if stream.params.has_key('extended') and stream.params['extended'].has_key('ffmpeg_coding_params'):
				ffmpeg_params = self.__mergeFfmpegParams(ffmpeg_params, stream.params['extended']['ffmpeg_coding_params'])

			#cmd = '%s "%s"'%(cmd, oFile)
			cmd = ffmpeg_path + ' ' + ' '.join(ffmpeg_params)
			self.__printCmd(cmd)
			if STTNGS['vc']:
				p = os.popen(cmd)
				p.close()

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
		rv[len(rv):] = ['-acodec', 'libfaac',
						'-ac', '2',
						'-ab', '%dk'%_ab,
						'-ar', '%d'%_ar]
		return rv

	def __audioFfmpegParamsTmpAc3(self, filename, _map, _ab, _ar, _threads):
		rv = self.__audioFfmpegParamsBase(fileName, _map)
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
		cmd = ffmpeg_path + ' ' + ' '.join(ffmpeg_params)
		self.__printCmd(cmd)
		if STTNGS['ac']:
			p = os.popen(cmd)
			if p.close() is not None:
				#cmd = ffmpeg_path + ' -y -i "%s" -map %s -vn -acodec ac3 -ab 448k  -ar %d  -ac 6 -threads %d ./tmp.ac3'%(iFile, stream[1], ar, STTNGS['threads'])
				tmp_fn = '%s/tmp.ac3'%STTNGS['temp_dir']
				ffmpeg_params = self.__audioFfmpegParamsTmpAc3(iFile, stream.trackID, 448, ar, STTNGS['threads'])
				ffmpeg_params.append('"%s"'%tmp_fn)
				cmd = ffmpeg_path + ' ' + ' '.join(ffmpeg_params)
				self.__printCmd(cmd)
				p = os.popen(cmd)
				p.close()
					
				#cmd = ffmpeg_path + ' -y -i ./tmp.ac3 -vn -acodec libfaac -ab %dk  -ar %d  -ac 2 -threads %d %s "%s"'%(ab, ar, STTNGS['threads'], add_params, oFile)
				ffmpeg_params = ffmpeg_params_add
				idx = ffmpeg_params.index('-i')
				ffmpeg_params[idx+1] = '"%s"'%tmp_fn
				idx = ffmpeg_params.index('-map')
				del ffmpeg_params[idx:idx+2]
				ffmpeg_params.append('"%s"'%oFile)

				if stream.params.has_key('extended') and stream.params['extended'].has_key('ffmpeg_coding_params'):
					ffmpeg_params = self.__mergeFfmpegParams(ffmpeg_params, stream.params['extended']['ffmpeg_coding_params'])

				cmd = ffmpeg_path + ' ' + ' '.join(ffmpeg_params)
				self.__printCmd(cmd)
				p = os.popen(cmd)
				p.close()
					
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
			if stream.params['extended'].has_key('copy'):
				print 'subtitle from .mp4 files allways copy'

			# TODO: extract or copy subtitles on ttxt format
			track_id = (int)(stream.trackID.split(self.mediainformer.mapStreamSeparatedSymbol(iFile))[1])+1

			fileName, fileExtension = os.path.splitext(iFile)
			tmpFile = oFile+fileExtension
			shutil.copyfile(iFile, tmpFile)
			#cmd = mp4box_path + ' -raw %d \"%s\"'%(track_id, tmpFile) # or can use -single instead of -raw
			cmd = mp4box_path + ' -single %d \"%s\"'%(track_id, tmpFile) # or can use -single instead of -raw
			self.__printCmd(cmd)
			p = os.popen(cmd)
			p.close()
			os.unlink(tmpFile)

			fileName, fileExtension = os.path.splitext(tmpFile)
			tmpFile = fileName + '_track%d'%track_id + fileExtension
			return tmpFile
		else:
			if isMatroshkaMedia(iFile) and stream.params.has_key('mkvinfo_trackNumber'):
				if stream.format().upper()=='ASS' or stream.format().upper()=='SSA':
					assFileName = oFile+'.ass'
					cmd = mkvtoolnix_path + 'mkvextract tracks "%s" %s:"%s"'%(iFile, stream.params['mkvinfo_trackNumber'], assFileName)
					self.__printCmd(cmd)
					if STTNGS['sc']:
						p = os.popen(cmd)
						p.close()
						sConverter = subConverter(STTNGS)
						sConverter.ass2ttxt(assFileName, oFile, prms)
						if STTNGS['ctf']:
							os.unlink(assFileName)
				else: # TODO: on mkv-files can be and other type's of subtitile
					strFileName = oFile+'.srt'
					cmd = mkvtoolnix_path + 'mkvextract tracks "%s" %s:"%s"'%(iFile, stream.params['mkvinfo_trackNumber'], strFileName)
					self.__printCmd(cmd)
					if STTNGS['sc']:
						p = os.popen(cmd)
						p.close()
						sConverter = subConverter(STTNGS)
						sConverter.srt2ttxt(strFileName, oFile)
						if STTNGS['ctf']:
							os.unlink(strFileName)
			else:
				tmpName = iFile.split('/')[-1]+'_%s.srt'%stream.trackID
				cmd = ffmpeg_path + ' -y -i "%s" -map %s -an -vn -sbsf mov2textsub -scodec copy "%s"'%(iFile, stream.trackID, tmpName)
				self.__printCmd(cmd)
				if STTNGS['sc']:
					p = os.popen(cmd)
					p.close()
					sConverter = subConverter(STTNGS)
					sConverter.ass2ttxt(tmpName, oFile)
					if STTNGS['ctf']:
						os.unlink(tmpName)
		return oFile


	def __streamFromFAdd(self, fadd, fi, currentTrack=0):
		path = os.path.dirname(fi.filename)+'/'
		nn = self.buildFN(fi.filename, fadd[1])
		if not nn[0] in '/~':
			nn = path+nn
		#ext = nn.split('.')[-1].lower()
		if not os.path.exists(nn):
			print 'file "%s" not exist'%nn
			sys.exit(1)
		_fi = self.mediainformer.fileInfo(nn)
		_fi.streams[0].params['GlobalTrackNum'] = currentTrack
		title = None
		if fadd[-1].has_key('title'):
			title = fadd[-1]['title']

		# get stream info
		stream = None
		if fadd[2].has_key('stream'):
			stream = _fi.streams[fadd[2]['stream']]
		else:
			for i in range(len(_fi.streams)):
				tmp_stream = _fi.streams[i]
				if tmp_stream.type==fadd[0]:
					stream = tmp_stream
					break
		if stream<>None:
			stream.params['extended'] = fadd[-1]
			stream.params['filename'] = _fi.filename
			stream.params['informer'] = _fi.informer
			stream.params['title'] = title
		return stream


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
				strms.append(int(s))

		# chech hardsub
		hardsub_streams = []
		for i in strms:
			stream = fi.streams[i]
			if stream.params.has_key('extended') and stream.params['extended'].has_key('hardsub'):
				stream.params['filename'] = fi.filename
				hardsub_stream.append(stream)
		for fadd in STTNGS['fadd']:
			stream = self.__streamFromFAdd(fadd, fi)
			if stream.params.has_key('extended') and stream.params['extended'].has_key('hardsub'):
				hardsub_streams.append(stream)

		sConverter = subConverter(STTNGS)
		currentTrack = 0
		out_fn = '%s/%s'%(STTNGS['temp_dir'], name)
		for i in strms:
			stream = fi.streams[i]
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
			if stream.params['title'] and stream.params['title']!='':
				stream.params['name'] = stream.params['title']
				if len(stream.params['title']):
					out_fn = '%s_%s'%(out_fn, stream.params['title'])

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

		addCmd2=''
		ve = ''
		ae = ''
		se = ''
		currentTrackIdx = 0
		trackID = 0
		if STTNGS['vv']:
			print
		info =  self.tagTrackInfo(name)
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
			addCmd2 += ' -add "%s":lang=%s'%(f[1], l,)
			#addCmd2 += ' -add "%s":lang=%s'%(string.replace(f[1], '0.0', '0:0'), l,)
			if delay!=0:
				addCmd2 += ':delay=%d'%delay
			if f[0]>0:
				addCmd2 += ':group=%d'%f[0]
			#if f[2][3].has_key('name'):
			#	addCmd2+=':name=%s'%f[2][1]
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

		name = STTNGS['temp_dir']+'/'+'.'.join(os.path.basename(fi.filename).split('.')[:-1])+'.'+STTNGS['format']
		cmd = mp4box_path + ' %s "%s" -new'%(addCmd2, name)
		self.__printCmd(cmd)
		if not STTNGS['mn']:
			p = os.popen(cmd)
			p.close()

		self.iTagger(name)

		mpeg4fixer().fixFlagsAndSubs(name, STTNGS['fd'])

		trackNames = []
		need = False
		for f in files:
			n = None
			if f[2]!=None and f[2].params.has_key('name'):
				n = unicode(f[2].params['name'], 'utf-8').encode('utf-8')
				need = True
			trackNames.append(n)
		if need:
			mpeg4fixer().setTrackNames(name, trackNames) 

		if STTNGS['ctf']:
			for f in files:
				os.unlink(f[1])

		return name


	def fileProcessing(self, fi):
		'''
			Processing one media file
		'''
		filename = fi.filename
		if STTNGS.has_key('tagging_mode'):
			self.iTagger(filename)
		else:
			filename = self.encodeMedia(fi)

		if STTNGS['web_optimization']:
			cmd = mp4box_path + ' -inter 500 "%s"'%filename
			self.__printCmd(cmd)
			p = os.popen(cmd)
			p.close()

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


#print sys.argv
#print sys.platform
#print os.path.dirname(sys.argv[0])
#sys.exit(1)



if __name__=='__main__':
	"""
	import struct
	print struct.pack('b', int('29', 16))
	correct_profile(sys.argv[1])
	sys.exit()
	"""

	#tmp = shlex.split("fagfsdf fsadf ads \"fasndifuds fsf asdf\" f\ fds")
	#tmp.append('asdq we')
	#print tmp
	#print ' '.join(tmp)
	#sys.exit(0)

	#os.environ['PYTHONIOENCODING'] = 'utf-8'

	converter = Video2iDevice()

	startTime = time.time()
	argv = sys.argv[1:]
	JSON_pipe = len(argv)==1 and argv[0]=='-json_pipe'
	if len(sys.argv)==1 or JSON_pipe:
		i, o, e = select.select([sys.stdin], [], [], 3)
		if i:
			if JSON_pipe:
				argv = json.JsonReader().read(sys.stdin.read())
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
			if type(val)==type(''):
				val = unicode(val, 'utf-8')
			if key=='TRACK_REGEX' or key=='TRACKS_REGEX':
				if not STTNGS.has_key(key):
					STTNGS[key] = val.split(';')
			else:
				if not STTNGS.has_key(key):
					STTNGS[key] = val
	#print STTNGS['subStyleColors']
	converter.getSettings(argv)

	if not STTNGS.has_key('threads'):
		STTNGS['threads'] = os.sysconf('SC_NPROCESSORS_CONF')

	if STTNGS['temp_dir'][-1]=='/':
		STTNGS['temp_dir'] = STTNGS['temp_dir'][:-1]
	if not os.path.exists(STTNGS['temp_dir']):
		print os.mkdir(STTNGS['temp_dir'])


	converter.mediainformer.artwork_path = STTNGS['temp_dir']

	for fn in STTNGS['files']:
		if STTNGS['vv']:
			print '\n------------------------ %s ------------------------'%fn
		if STTNGS.has_key('info'):
			fi = converter.mediainformer.fileInfo(fn)
			#fi.streams = map(lambda x: [x.type, x.trackID[x.trackID.index(converter.mediainformer.mapStreamSeparatedSymbol(fi.filename))+1:], x.language, x.params], fi.streams)
			#print type(fi['streams'][2][1])
			#sys.exit()
			print json.write(fi.dump('dict'))
		else:
			if STTNGS['streams']=='none':
				#fi = {'filename': fn, 'informer': 'no need'}
				fi = cMediaInfo('no need', fn)
			else:
				fi = converter.mediainformer.fileInfo(fn)
			converter.fileProcessing(fi)

	#os.system('date')
	tm = time.time()-startTime
	if not (STTNGS.has_key('info') and not STTNGS['vv']):
		print 'time %02d:%02d:%02d'%(tm/60/60, tm%(60*60)/60, tm%60)
