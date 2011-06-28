#!/usr/bin/env python
# -*- coding: utf-8 -*-

# writed by derand (http://derand.blogspot.com)
# - Sorry for horrible code -

# thanks:
#   http://ffmpeg.org/ffmpeg-doc.html
#   http://www.linux.org.ru/forum/desktop/3597304
#   http://theapplegeek.ru/archives/3800
#   http://streaming411.com/wiki/index.php?title=Encoding_prerecorded_video
#   http://atomicparsley.sourceforge.net
#


#####################  #########################
#valid
#cabac=0 / ref=5 / deblock=1:0:0 / analyse=0x1:0x131 / me=umh / subme=6 / psy=1 / psy_rd=0.0:0.0 / mixed_ref=0 / me_range=16 / chroma_me=1 / trellis=0 / 8x8dct=0 / cqm=0 / deadzone=21,11 / chroma_qp_offset=0 / threads=1 / nr=0 / decimate=1 / mbaff=0 / constrained_intra=0 / bframes=0 / wpredp=0 / keyint=240 / keyint_min=24 / scenecut=40 / rc_lookahead=40 / rc=crf / mbtree=1 / crf=12.8 / qcomp=0.60 / qpmin=10 / qpmax=51 / qpstep=4 / vbv_maxrate=1500 / vbv_bufsize=2000 / ip_ratio=1.40 / aq=1:1.00

#invalid
#cabac=0 / ref=5 / deblock=1:0:0 / analyse=0x1:0x111 / me=dia / subme=5 / psy=1 / psy_rd=0.00:0.00 / mixed_ref=0 / me_range=16 / chroma_me=1 / trellis=0 / 8x8dct=0 / cqm=0 / deadzone=21,11 / fast_pskip=1 / chroma_qp_offset=0 / threads=3 / sliced_threads=0 / nr=0 / decimate=1 / interlaced=0 / constrained_intra=0 / bframes=0 / weightp=0 / keyint=300 / keyint_min=25 / scenecut=40 / intra_refresh=0 / rc_lookahead=40 / rc=2pass / mbtree=1 / bitrate=650 / ratetol=6.2 / qcomp=0.60 / qpmin=15 / qpmax=51 / qpstep=4 / cplxblur=20.0 / qblur=0.5 / vbv_maxrate=650 / vbv_bufsize=600 / ip_ratio=1.41 / aq=1:1.00 / nal_hrd=none

#at first pass add ref=1:subme=2:me=dia:analyse=none:trellis=0:no-fast-pskip=0:8x8dct=0:weightb=0
# -flags2 +dct8x8-fastpskip-dct8x8-wpred -subq 6

#Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
#Style: Default,Trebuchet MS,50, &H00FFFFFF,&H0000FFFF,&H000F0991, &H00000000, 0,0,0,0,100,95,0,0,1,3,0,2,35,35,20,204
#Style: Default 2,Trebuchet MS,50,&H00FFFFFF,&H0000FFFF,&H000F0991,&H00000000, 0,0,0,0,100,95,0,0,1,3,0,8,35,35,20,204


'''
HandBrakeCLI --ipod-atom --encoder x264 --vb 450 --two-pass --rate 23.976 \
--x264opts "partitions=+parti4x4+partp8x8+partb8x8:subq=5:trellis=1:me_range=16:keyint_min=25:qcomp=0.7:level=30" \
--audio 1,2 --aencoder faac,faac --ab 128,128 --mixdown dpl2,dpl2 --arate 48,48 --aname Japanise,Russian \
--width 480 --height 240  --srt-file ./sub_rus.srt --srt-default 1 --srt-lang Russian -i ./video_.mp4 -o ./e01_.m4v


HandBrakeCLI -f mp4 --encoder x264 --vb 450 --two-pass --rate 23.976 \
--x264opts cabac=0:ref=5:me=umh:bframes=0:subme=6:8x8dct=0:trellis=0 \
--audio 1,2 --aencoder faac,faac --ab 128,128 --mixdown stereo,stereo --arate 48,48 --aname Japanise,Russian -D 0.0 \
--width 480 --height 240  --srt-file ./sub_rus.srt --srt-default 1 --srt-lang rus -i ./video_.mp4 -o ./e01_.m4v
'''

import sys
import os
import re
import getopt
import glob
import string
import json
import os.path

from subConverter import subConverter
from mpeg4fixer import mpeg4fixer

STTNGS = {
#	'threads':	3,
	'files':	[],
	'mn':		False,
	'ac':		True,
	'vc':		True,
	'sc':		True,
	'lang':		'',
	'ar':		48000,
	'ab':		128,
	'b':		640,
	'refs':		2,
	'tn':		False,
	'streams':	'',
	'tfile':	'',
	'fd':		False,
	'fadd':		[],
	'vq':		3,
	'format':	'm4v',
	'add2TrackIdx': 0,
	'version' : '0.5.2',
	'vcopy':	False,
	'acopy':	False,
}

help = '''
converter video for iPhone/iPod Touch/iPad
for work script you should install ffmpeg with x264 codec (http://derand.blogspot.com/2009/06/ffmpeg-x264.html),
MP4Box (http://gpac.sourceforge.net/doc_mp4box.php)
and AtomicParsley (http://atomicparsley.sourceforge.net)
Usage
  ./2iDevice.py [options] inputFile[s]

Options
	-h			this help
	-th		[int]	using threads for coding
	-lang		[str]	languages of srteams separated ':'
	-cn			disable converting step, merge streams files to .m4v file
	-vn			disable convert video
	-an			disable convert audio
	-sn			disable convert subtitles
	-ar		[int]	audio rate (def 48000)
	-ab		[int]	audio bitrate (def 128k)
	-b		[int]	video bitrate (def 640)
	-refs		[int]	ref frames for coding video
	-tn			disable sets tags
	-mn			disable merge
	-streams	[str]	select streams numbers (first index 0 separated ':')
	-tfile		[str]	set tags file
	-track		[int]	track
	-tracks		[int]	tracks count
	-sfile		[str]	set subtitle filename. If not set try search in current dir. 
				Can be format:
					[NAME] - origin name of file
					[2EID] - episode id (evaluate from regext in tfile)
					[2EC] - episode count
	-rename2	[str]	rename result file to. supports tags: [SEASON], [EPISODE_ID]
	-fd			fix video duration
	-et		[str]	set episodes titles separated ';'
	-stik		[str]	set iTunes stick. can be 'Movie', 'Music Video', 'TV Show' ... (see: AtomicParsley --stik-list)
	-TVShowName	[str]	set showname tag
	-TVSeasonNum	[str]	set season num
	-description	[str]	set deascription
	-year		[str]	set year
	-artwork	[str]	set artwork filename
	-TRACK_REGEX	[srt]	set regular exeption for select track from filename
	-TRACKS_REGEX	[srt]	set regular exeption for select tracks from filename
	-vq		[int]	(deprecated: use -s) video quality (1 - 480x*,   2 - *x320, 3 - max)
	-format		[str]	output format (default: 'm4v')
	-flexibleTime	[str]	flex time subtitles (format:'0:22:03.58->0:21:10.00;0:02:28.69->0:02:22.85')
	-stream		[int]	stream idx from appending files (vfile, afile, sfile)
	-title		[srt]	stream title from appending files (vfile, afile, sfile)
	-add2TrackIdx	[int]	add to track (def: 0)
	-s		[int]x[int]	result resolution, can looks like ('*x320', '960x*')
	-v			script version
	-passes    [str] video passes coding separeted ':'
	-r         [str] frame rate
	-addTimeDiff [int] add time(ms) diff to subs (last sub stream)
	-vcopy			copy video stream
	-acopy			copy audio stream
	
Author
	Writen by Andrew Derevyagin (2derand+2idevice@gmail.com)

Copyright
	Copyright © 2010 Andrey Derevyagin
  
Bugs
	If you feel you have found a bug in "2iDevice", please email me 2derand+2idevice@gmail.com
'''


#black_list = ('EdKara', 'TVLpaint', 'SerialMainTitle', 'Kar_OP_1', 'Kar_OP_2', 'Kar_OP_3', 'Kar_OP_4', 'Kar_ED_1', 'Kar_ED_2', 'Kar_ED_3', 'Kar_ED_4', 'Kar_ED_5', 'Kar_ED_6' )





def printCmd(cmd):
	print ': \033[1;32m%s\033[00m'%cmd

def getSettings():
	ckey = 'files'
	saveP = False
	waitParam = False
	for el in sys.argv[1:]:
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
			if ckey=='vcopy':
				STTNGS['vcopy'] = True
				saveP = True
			if ckey=='acopy':
				STTNGS['acopy'] = True
				saveP = True
			if ckey=='tn' or ckey=='mn':
				STTNGS[ckey] = True
				saveP = True
			if ckey=='fd':
				STTNGS['fd'] = True
				saveP = True
			if ckey=='addTimeDiff':
				waitParam = True
			if ckey=='h':
				print help
				sys.exit(0)
			if ckey=='v':
				print "Version: %s"%STTNGS['version']
				sys.exit(0)
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
			elif ckey=='flexibleTime':
				'''
					format '0:22:03.58->0:21:10.00;0:02:28.69->0:02:22.85'
				'''
				tmp = re.search('(\d{1,2}:\d{2}:\d{2}.\d{2})\s*\-\>\s*(\d{1,2}:\d{2}:\d{2}.\d{2})\s*\;(\d{1,2}:\d{2}:\d{2}.\d{2})\s*\-\>\s*(\d{1,2}:\d{2}:\d{2}.\d{2})', el)
				if tmp:
					t = [(tmp.group(1), tmp.group(2)), (tmp.group(3), tmp.group(4))]
					tmp = STTNGS['fadd']
					if len(tmp)>0:
						if tmp[-1][0]==2:
							tmp[-1][-1]['flexibleTime'] = t
					else:
						# parametr before [v,a,s]file parametr 
						pass
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
			else:
				if STTNGS.has_key(ckey):
					if type(STTNGS[ckey])==type([]):
						STTNGS[ckey].append(el)
					elif type(STTNGS[ckey])==type(123):
						STTNGS[ckey] = int(el)
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
	print STTNGS

def loadSettingsFile(filename):
	file = 0 
	try:
		file = open(filename, 'r')
	except:
		print 'error open file %s'%filename
		sys.exit(1)
	inside_key = False
	save_key=''
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
					print _tmp
					rv[save_key] = json.loads(_tmp)
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
					rv[key] = json.loads(val)
				else:
					save_key  =key
					_tmp = val
					inside_key = True
			else:
				rv[key] = val
	return rv

def fileInfoUsingFFMPEG(filename):
	rv = {}
	searchString = 'Stream #'
	rv['filename'] = filename
	rv['informer'] = 'ffmpeg'
	streams = []
	p = os.popen('ffmpeg -i "%s" 2>&1'%filename)
	print 'ffmpeg -i "%s" 2>&1'%filename
	for line in p.readlines():
		if line.find(searchString)>-1:
			l = line[line.find(searchString)+len(searchString):-1]
			i=0
			while i<len(l) and l[i]!=':' and l[i]!='(':
				i+=1
			name = l[:i]
			name = re.sub(r'\[[^\]]*\]', '', name)
			lng = None
			if l[i]=='(':
				while l[i]!=')':
					i+=1
				lng = l[len(name)+1:i]
				i+=1
			i+=2
			l = l[i:]
			i = l.find(':')
			t = l[:i]
			l = l[i+2:]
			tp = -1
			prms = {}
			if t == 'Video':
				tp = 0
				info = l.split(', ')
				prms['codec'] = info[0]
				prms['colorFormat'] = info[1]
				res = info[2]
				prms['resolution'] = res
				w = res[:res.find('x')]
				res = res[len(w)+1:]
				if res.find(' ')>-1:
					res = res[:res.find(' ')]
				h = res
				prms['width'] = int(w)
				prms['height'] = int(h)
				#prms['bitrate'] = info[3]
			elif t == 'Audio':
				tp = 1
				info = l.split(', ')
				prms['codec'] = info[0]
				frequency = info[1]
				if frequency.find(' '):
					frequency = frequency[:frequency.find(' ')]
				prms['frequency'] = int(frequency)
				channels = info[2]
				if channels=='stereo' or channels=='2 channels':
					channels = '2'
				prms['channels'] = channels
				if len(info)>4:
					bitrate = info[4]
					if bitrate.find(' '):
						bitrate = bitrate[:bitrate.find(' ')]
					prms['bitrate'] = int(bitrate)
			elif t == 'Subtitle':
				tp = 2
				info = l.split(', ')
				prms['codec'] = info[0]
			else:
				continue
			
			streams.append([tp, name, lng, prms, ])
			print line[:-1]
	rv['streams'] = streams
	return rv

def fileInfoUsingMKV(filename):
	def mkvInfoKeyValue(line):
		tmp = line.split(':')
		if len(tmp)==1:
			return (tmp[0].strip(), None)
		return (tmp[0].strip(), ':'.join(tmp[1:]).strip())

	rv = {}
	rv['filename'] = filename
	rv['informer'] = 'mkvinfo'
	streams = []
	inTrackSegment = False
	p = os.popen('mkvinfo "%s" 2>&1'%filename)
	streamType = None
	trackID = None
	lang = None
	prms = {}
	trackNumber = 0
	for line in p.readlines():
		line = line[:-1]
		if len(line)>2 and line[:2]=='|+':
			val = line[2:].strip()
			inTrackSegment = (val=='Segment tracks')
		tmp = re.search('\|\s*\+(.*)', line)
		if tmp:
			tmp = tmp.group(1).strip()
			if tmp == 'A track':
				if streamType!=None:
					if lang==None:
						lang = 'und'
					streams.append([streamType, trackID, lang, prms, ])
					streamType = None
					trackID = None
					lang = None
					prms = {}
			if inTrackSegment:
				(key, val) =  mkvInfoKeyValue(tmp)
				if key=='Track number':
					#trackID = '0.%d'%(int(val)-1)
					trackID = '0.%d'%trackNumber
					trackNumber = trackNumber+1
					prms['mkvinfo_trackNumber'] = val
				elif key=='Track type':
					if val=='video':
						streamType=0
					elif val=='audio':
						streamType=1
					elif val=='subtitles':
						streamType=2
				elif key=='Language':
					lang = val
				elif key=='Language':
					lang = val
				elif key=='Codec':
					prms['codec'] = val
				elif key=='Pixel width':
					prms['width'] = int(val)
				elif key=='Pixel height':
					prms['height'] = int(val)
				elif key=='Codec ID':
					prms['codec'] = val
				elif key=='Sampling frequency':
					prms['frequency'] = int(val)
				elif key=='Output sampling frequency':
					prms['frequency'] = int(val)
				elif key=='Channels':
					prms['channels'] = val
				elif key=='Name':
					prms['name'] = val
				elif key=='Display width':
					prms['dwidth'] = int(val)
				elif key=='Display height':
					prms['dheight'] = int(val)
	if streamType!=None:
		if lang==None:
			lang = 'und'
		streams.append([streamType, trackID, lang, prms, ])
	rv['streams'] = streams
	return rv

def fileInfo(filename):
	'''
		input: video file name
		output:
			{
				'filename': filename
				'streams': 
					[
						[
							streamType,			// 0 - video, 1 - audio, 2 - subs
							trackID,			// track id
							lang,				// language
							params = []			// additional params
						],
						...	
					] 
			}
	'''
	#print filename.split('.')[-1].lower()
	#sys.exit(0)
	ext = filename.split('.')[-1].lower()
	rv = {}
	if ext=='mkv' or ext=='mka':
		rv = fileInfoUsingMKV(filename)
	elif ext=='ass':
		rv = {
			'informer': 'ffmpeg',
			'filename': filename,
			'streams' : [[2, '0.0', None, {'codec': 'ass'}]]
			}
	else:
		rv = fileInfoUsingFFMPEG(filename)
	return rv

def getLang(i, lng=None):
	langs = STTNGS['lang'].split(':')
	if len(langs)>i and langs[i]!='':
		return (langs[i],i+1)
	if lng==None or lng=='':
		return ('und', i+1)
	return (lng, i+1)

def tagTrackInfo(fn):
	srch = None
	tr = None
	if STTNGS.has_key('track'):
		tr = int(STTNGS['track'])
	if STTNGS.has_key('TRACK_REGEX'):
		for p in STTNGS['TRACK_REGEX']:
			srch = re.compile(p).search(fn)
			if srch!=None:
				break
		if srch!=None:
			tr = int(srch.groups()[0])+STTNGS['add2TrackIdx']
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
	return (tr, trs)

def iTagger(fn):
	prms = ' --copyright "derand"'
	if not STTNGS['tn']:
		if STTNGS.has_key('artwork'):
			prms += ' --artwork "%s"'%STTNGS['artwork']
		if STTNGS.has_key('stik'):
			prms += ' --stik "%s"'%STTNGS['stik']
		if STTNGS.has_key('TVShowName'):
			prms += ' --TVShowName "%s"'%STTNGS['TVShowName']
			prms += ' --album "%s"'%STTNGS['TVShowName']
			prms += ' --artist "%s"'%STTNGS['TVShowName']
		if STTNGS.has_key('TVSeasonNum'):
			prms += ' --TVSeasonNum "%s"'%STTNGS['TVSeasonNum']
		(track, tracks) = tagTrackInfo(fn)
		if track!=None:
			print track, tracks
			if tracks!=None:
				prms += ' --tracknum %d/%d --TVEpisodeNum %d'%(track, tracks, track)
			else:
				prms += ' --tracknum %d --TVEpisodeNum %d'%(track, track)
			if STTNGS.has_key('episodes_titles') and len(STTNGS['episodes_titles'])>(track-1):
				prms += ' --TVEpisode "%s"'%STTNGS['episodes_titles'][track-1]
				prms += ' --title "%s"'%STTNGS['episodes_titles'][track-1]
			else:
				prms += ' --TVEpisode "%s"'%fn
		if STTNGS.has_key('description'):
			prms += ' --description "%s"'%STTNGS['description']
		if STTNGS.has_key('year'):
			prms += ' --year "%s"'%STTNGS['year']
		if prms.find(' --artist ')==-1 and STTNGS.has_key('artist'):
			prms += ' --artist "%s"'%STTNGS['artist']
	prms += ' --encodingTool "2iDevice.py (http://derand.blogspot.com)" --overWrite'
	cmd = 'AtomicParsley "%s" %s'%(unicode(fn,'UTF-8'), prms)
	printCmd(cmd)
	os.system(cmd.encode('utf-8'))

def buildFN(baseFN, convertFN):
	rv = convertFN
	if rv.find('[NAME]')>-1:
		nm = '.'.join(os.path.basename(baseFN).split('.')[:-1])
		rv = rv.replace('[NAME]', nm)
	(track, tracks) = tagTrackInfo(baseFN)
	if rv.find('[2EID]')>-1:
		if track!=None:
			rv = rv.replace('[2EID]', '%02d'%track)
	if rv.find('[2EC]')>-1:
		if tracks!=None:
			rv = rv.replace('[2EC]', '%02d'%tracks)
	return rv

def rename(fn):
	if not STTNGS.has_key('rename2'):
		return None
	name = STTNGS['rename2']
	(tr, trs) = tagTrackInfo(fn)
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
	printCmd(cmd)
	os.system(cmd)

def sizeConvert(real1, real2, out1):
	out2 = (real2*out1)/real1
	if out2%16>7:
		out2 += 16-out2%16
	else:
		out2 -= out2%16
	return (out1, out2)

def cVideo(iFile, stream, oFile):
	w = stream[3]['width']
	h = stream[3]['height']
	if stream[3].has_key('dwidth'): w = stream[3]['dwidth']
	if stream[3].has_key('dheight'): h = stream[3]['dheight']
	
	if STTNGS.has_key('s'):
		res = STTNGS['s'].split('x')
		if res[0]=='*':
			(_h, _w) = sizeConvert(h, w, int(res[1]))
		elif res[1]=='*':
			(_w, _h) = sizeConvert(w, h, int(res[0]))
		else:
			_w = int(res[0])
			_h = int(res[1])
	else:
		if STTNGS['vq']==1:
			(_w, _h) = sizeConvert(w, h, 480)
		elif STTNGS['vq']==2:
			(_h, _w) = sizeConvert(h, w, 320)
		else:
			(_w, _h) = sizeConvert(w, h, 480)
			if _h<320:
				(_h, _w) = sizeConvert(h, w, 320)

	print '\033[1;33m %dx%d  ==> %dx%d \033[00m'%(w,h, _w,_h)

	passes = [1,2]
	if STTNGS.has_key('passes'):
		passes = []
		for el in STTNGS['passes'].split(':'):
			passes.append(int(el))

	if STTNGS['vcopy']:
		passes = [1]

	for _pass in passes:
		if STTNGS['vcopy']:
			cmd = 'ffmpeg -y -i "%s" -map %s -an -vcodec copy -threads %d'%(iFile, stream[1], STTNGS['threads'] )
		else:
			cmd = 'ffmpeg -y -i "%s" -pass %d -map %s -an  -vcodec "libx264" -b "%d k" -s "%dx%d" -flags "+loop" -cmp "+chroma" -partitions "+parti4x4+partp8x8+partb8x8" -subq 6  -trellis 0  -refs %d  -coder 0  -me_range 16  -g 240   -keyint_min 25  -sc_threshold 40 -i_qfactor 0.71 -maxrate  "%d k" -bufsize "1000 k" -rc_eq "blurCplx^(1-qComp)" -qcomp 0.6 -qmin 15 -qmax 51 -qdiff 4 -flags2 "+bpyramid-mixed_refs+wpred-dct8x8+fastpskip" -me_method full -directpred 2 -b_strategy 1 -level 30 -threads %d'%(iFile, _pass, stream[1], STTNGS['b'], _w,_h, STTNGS['refs'], STTNGS['b'], STTNGS['threads'] )
			if STTNGS.has_key('r'):
				cmd = '%s -r %s'%(cmd, STTNGS['r'])
		cmd = '%s "%s"'%(cmd, oFile)
		printCmd(cmd)
		if STTNGS['vc']:
			p = os.popen(cmd)
			p.close()

def cAudio(iFile, stream, oFile):
	ar = STTNGS['ar']
	ab = STTNGS['ab']
	if stream[3].has_key('extended'):
		if stream[3]['extended'].has_key('ar'):
			ar = stream[3]['extended']['ar']
		if stream[3]['extended'].has_key('ab'):
			ar = stream[3]['extended']['ab']
	if stream[3].has_key('frequency') and ar>stream[3]['frequency']:
		ar = stream[3]['frequency']
	if stream[3].has_key('bitrate') and ab>stream[3]['bitrate']:
		ab = stream[3]['bitrate']

	cmd = None
	if STTNGS['acopy'] or (stream[3].has_key('codec') and stream[3]['codec']=='aac' and stream[3].has_key('channels') and stream[3]['channels']=='2' and stream[3].has_key('bitrate') and stream[3]['bitrate']==ab and stream[3].has_key('frequency') and stream[3]['frequency']==ar):
		cmd = 'ffmpeg -y -i "%s" -map %s -vn -acodec copy "%s"'%(iFile, stream[1], oFile)
	else:
		cmd = 'ffmpeg -y -i "%s" -map %s -vn -acodec libfaac -ab %dk -ac 2 -ar %d -threads %d -strict experimental "%s"'%(iFile, stream[1], ab, ar, STTNGS['threads'], oFile)

	#cmd = 'ffmpeg -y -i "%s" -map %s -vn -acodec copy -strict experimental "%s"'%(iFile, stream[1], oFile)
	printCmd(cmd)
	if STTNGS['ac']:
		p = os.popen(cmd)
		if p.close() is not None:
			cmd = 'ffmpeg -y -i "%s" -map %s -vn -acodec ac3 -ab 448k  -ar %d  -ac 6 -threads %d ./tmp.ac3'%(iFile, stream[1], ar, STTNGS['threads'])
			printCmd(cmd)
			p = os.popen(cmd)
			p.close()
					
			cmd = 'ffmpeg -y -i ./tmp.ac3 -vn -acodec libfaac -ab %dk  -ar %d  -ac 2 -threads %d "%s"'%(ab, ar, STTNGS['threads'], oFile)
			printCmd(cmd)
			p = os.popen(cmd)
			p.close()
					
			os.remove('./tmp.ac3')

def cSubs(iFile, stream, informer, prms, oFile):
	ext = iFile.split('.')[-1].lower()
	if ext=='srt':
		if STTNGS['sc']:
			sConverter = subConverter(STTNGS)
			sConverter.srt2ttxt(iFile, oFile, prms)
	elif ext=='ass' or ext=='ssa':
		print iFile, stream, informer, prms, oFile
		if STTNGS['sc']:
			sConverter = subConverter(STTNGS)
			sConverter.ass2ttxt(iFile, oFile, prms)
	elif ext=='ttxt':
		pass
	else:
		print '4',informer,stream
		if informer=='mkvinfo':
			if stream[3]['codec']=='S_TEXT/ASS':
				tmpName = '%s_%s.ass'%(iFile.split('/')[-1], stream[1])
				print tmpName
				cmd = 'mkvextract tracks "%s" %s:"%s"'%(fi['filename'], stream[3]['mkvinfo_trackNumber'], tmpName)
				printCmd(cmd)
				if STTNGS['sc']:
					p = os.popen(cmd)
					p.close()
					sConverter = subConverter(STTNGS)
					sConverter.ass2ttxt(tmpName, oFile, prms)
			else:
				strFileName = re.compile('\\.ttxt$').sub('.srt', oFile)
				cmd = 'mkvextract tracks "%s" %s:"%s"'%(fi['filename'], stream[3]['mkvinfo_trackNumber'], strFileName)
				printCmd(cmd)
				if STTNGS['sc']:
					p = os.popen(cmd)
					p.close()
					sConverter = subConverter(STTNGS)
					sConverter.srt2ttxt(strFileName, oFile)
		else:
			tmpName = iFile.split('/')[-1]+'_%s.srt'%stream[1]
			cmd = 'ffmpeg -y -i "%s" -map %s -an -vn -sbsf mov2textsub -scodec copy "%s"'%(fi['filename'], stream[1], tmpName)
			printCmd(cmd)
			if STTNGS['sc']:
				p = os.popen(cmd)
				p.close()
				sConverter = subConverter(STTNGS)
				sConverter.ass2ttxt(tmpName, oFile)


def encodeStreams(fi):
	print fi
	name = os.path.basename(fi['filename'])
	files = []
	addCmd = ''
	addIdx = 0
	findSubs = True	
	(ve, ae, se) = ('', '', '')
	tmp = STTNGS['streams']
	strms = []
	if tmp=='' or tmp=='all':
		for i in range(len(fi['streams'])):
			strms.append(i)
	else:
		for s in tmp.split(':'):
			strms.append(int(s))
	sConverter = subConverter(STTNGS)
	for i in strms:
		stream = fi['streams'][i]
		print stream
		if stream[0]==0:
			files.append((0,name+'_%s.mp4'%stream[1], stream))
			cVideo(fi['filename'], stream, files[-1][1])

		elif stream[0]==1:
			files.append((1,name+'_%s.aac'%stream[1], stream))
			cAudio(fi['filename'], stream, files[-1][1])

		elif stream[0]==2:
			srtName = name+'_%s.ttxt'%stream[1]
			files.append((2,srtName, stream))
			cSubs(fi['filename'], stream, fi['informer'], {}, files[-1][1])
			findSubs = False
		addIdx+=1
	
	# add subs
	path = os.path.dirname(fi['filename'])+'/'
	nm = '.'.join(os.path.basename(fi['filename']).split('.')[:-1])
	for add in STTNGS['fadd']:
		nn = '%s%s'%(path, buildFN(fi['filename'], add[1]))
		ext = nn.split('.')[-1].lower()
		if not os.path.exists(nn):
			print 'file "%s" not exist'%nn
			sys.exit(1)
		print add[0], ext, nn
		_fi = fileInfo(nn)
		title = None
		if add[-1].has_key('title'):
			title = add[-1]['title']
		if add[0]==0:
			stream = None
			if add[2].has_key('stream'):
				stream = _fi['streams'][add[2]['stream']]
			else:
				for i in range(len(_fi['streams'])):
					stream = _fi['streams'][i]
					if stream[0]==add[0]:
						break
			tmp_fn = '%s.mp4'%os.path.basename(nn)
			stream[3]['extended'] = add[-1]
			if title and title!='':
				stream[3]['name'] = title
				if len(title):
					tmp_fn = '%s_%s.mp4'%(os.path.basename(nn), title)
			files.append((0, tmp_fn, stream))
			cVideo(nn, stream, files[-1][1])

		elif add[0]==1:
			stream = None
			if add[2].has_key('stream'):
				stream = _fi['streams'][add[2]['stream']]
			else:
				for i in range(len(_fi['streams'])):
					stream = _fi['streams'][i]
					if stream[0]==add[0]:
						break
			tmp_fn = '%s.aac'%os.path.basename(nn)
			stream[3]['extended'] = add[-1]
			if title!=None:
				stream[3]['name'] = title
				if len(title):
					tmp_fn = '%s_%s.aac'%(os.path.basename(nn), title)
			files.append((1,tmp_fn, stream))
			cAudio(nn, stream, files[-1][1])

		elif add[0]==2:
			stream = None
			if add[2].has_key('stream'):
				stream = _fi['streams'][add[2]['stream']]
			else:
				for i in range(len(_fi['streams'])):
					stream = _fi['streams'][i]
					if stream[0]==add[0]:
						break
			tmp_fn = '%s.ttxt'%os.path.basename(nn)
			stream[3]['extended'] = add[-1]
			if title and title!='':
				stream[3]['name'] = title
				if len(title):
					tmp_fn = '%s_%s.ttxt'%(os.path.basename(nn), title)
			files.append((2,tmp_fn, stream))
			cSubs(nn, stream, _fi['informer'], add[2], files[-1][1])
			findSubs = False
	
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
	
			
	print 'files: ',files

	addCmd2=''
	ve = ''
	ae = ''
	se = ''
	addIdx = 0
	for f in files:
		if f[2]!=None:
			(l, addIdx) = getLang(addIdx, f[2][2])
		else:
			(l, addIdx) = getLang(addIdx)
		addCmd2 += ' -add "%s":lang=%s'%(f[1], l,)
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

	name = './'+'.'.join(os.path.basename(fi['filename']).split('.')[:-1])+'.'+STTNGS['format']
	cmd = 'MP4Box %s "%s" -new'%(addCmd2, name)
	printCmd(cmd)
	if not STTNGS['mn']:
		p = os.popen(cmd)
		p.close()

	iTagger(name)

	mpeg4fixer().fixFlagsAndSubs(name, STTNGS['fd'])

	trackNames = []
	need = False
	for f in files:
		n = None
		if f[2]!=None and f[2][3].has_key('name'):
			n = unicode(f[2][3]['name'], 'utf-8').encode('utf-8')
			need = True
		trackNames.append(n)
	if need:
		mpeg4fixer().setTrackNames(name, trackNames) 

	rename(name)

#print sys.argv
#print sys.platform
#print os.path.dirname(sys.argv[0])
#sys.exit(1)

if __name__=='__main__':
	yep = False
	for el in sys.argv[1:]:
		if yep:
			STTNGS['tfile'] = el
			break
		if el=='-tfile':
			yep = True
	if len(STTNGS['tfile'])>0:
		TAGS = loadSettingsFile(STTNGS['tfile'])
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
	getSettings()
	
	if not STTNGS.has_key('threads')
		STTNGS['threads'] = os.sysconf('SC_NPROCESSORS_CONF')

	for fn in STTNGS['files']:
		print '\n------------------------ %s ------------------------'%fn
		fi = fileInfo(fn)
		encodeStreams(fi)

	os.system('date')


