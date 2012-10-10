#!/usr/bin/env python
# -*- coding: utf-8 -*-

# writed by derand


import sys
import os
import xml.parsers.expat
import re
import fileCoding
import math
from subprocess import Popen, PIPE, STDOUT

from v2d_utils import *


def isMatroshkaMedia(file_name):
	_, file_ext = os.path.splitext(file_name)
	file_ext = file_ext.lower()
	return file_ext in ['.mkv', '.mk3d', '.mka', '.mks']


class cStream(object):
	"""docstring for cStream"""
	def __init__(self, stream_type, trackID, language, params):
		super(cStream, self).__init__()
		self.type = stream_type
		self.trackID = trackID
		self.language = language
		self.params = params

	def __str__(self):
		rv = ''
		if self.type==0:
			rv += 'Video:'
		if self.type==1:
			rv += 'Audio:'
		if self.type==2:
			rv += 'Subtitle:'
		if self.type==3:
			rv += 'Image:'
		rv += ' %s'%self.trackID
		rv += ', %s'%self.language
		return 'cStream %s'%rv

	def dump(self, mode='string'):
		if mode=='string':
			rv = ''
			if self.type==0:
				rv += 'Video stream:\n'
			if self.type==1:
				rv += 'Audio stream:\n'
			if self.type==2:
				rv += 'Subtitle stream:\n'
			if self.type==3:
				rv += 'Image:\n'
			rv += 'Track ID: %s\n'%self.trackID.rjust(32)
			val = '%s'%self.language
			rv += 'Language: %s\n'%val.rjust(32)
			for key in sorted(self.params.keys()):
				val = '%s'%self.params[key]
				rv += '%s: %s\n'%(key, val.rjust(40-len(key)))
			return rv
		if mode=='dict':
			return {
			'type': self.type,
			'trackID': self.trackID[self.trackID.index(':')+1:],
			'language': self.language,
			'params': self.params
			}

	def format(self):
		rv = ''
		if self.params.has_key('Format'):
			rv = self.params['Format']
		if self.params.has_key('codec'):
			rv = self.params['codec']
		if self.type==2 and rv.upper()=='UTF-8' and self.params.has_key('Codec_ID') and self.params['Codec_ID'].upper()=='S_TEXT/UTF8':
			rv = 'srt'
		return rv

class cMediaInfo(object):
	"""docstring for cMediaInfo"""
	def __init__(self, informer, filename):
		super(cMediaInfo, self).__init__()
		self.informer = informer
		self.filename = filename
		self.streams = []
		self.tags = {}
		self.general = {}
		self.chapters = []   # not used yet

	def stream_add(self, stream):
		self.streams.append(stream)

	def __str__(self):
		rv = 'cMediaInfo(%s, \"%s\"):'%(self.informer, self.filename)
		for stream in self.streams:
			rv = rv + ', %s'%stream
		return rv

	def dump(self, mode='string'):
		if mode=='string':
			rv = 'Informer:\t%s\nFile Name:\t%s\n\n'%(self.informer, self.filename)
			if len(self.general.keys()):
				rv += 'General:\n'
				for key in sorted(self.general.keys()):
					val = '%s'%self.general[key]
					rv += '%s: %s\n'%(key, val.rjust(40-len(key)))
				rv += '\n'

			for stream in self.streams:
				rv += '%s\n'%stream.dump(mode)

			if len(self.chapters):
				rv += 'Chapters:\n'
				for ch in self.chapters:
					rv += '%s\n'%ch.dump(mode)

			if len(self.tags.keys()):
				rv += 'Tags:\n'
				for key in sorted(self.tags.keys()):
					val = '%s'%self.tags[key]
					rv += '%s: %s\n'%(key, val.rjust(40-len(key)))
			return rv
		if mode=='dict':
			streams_arr = []
			for s in self.streams:
				streams_arr.append(s.dump(mode))
			chapters_arr = []
			for c in self.chapters:
				chapters_arr.append(c.dump(mode))
			return {
			'informer': self.informer,
			'filename': self.filename,
			'streams': streams_arr,
			'tags': self.tags,
			'general': self.general,
			'chapters': chapters_arr
			}

	def video_stream(self):
		for stream in self.streams:
			if stream.type==0:
				return stream
		return None


class cChapter(object):
	"""docstring for cChapter"""
	def __init__(self, time_str, title):
		super(cChapter, self).__init__()
		self.time = self.__convertTimeString(time_str)
		self.title = title

	def __convertTimeString(self, time_str):
		''' _00_00_28920 '''
		_hours = _min = _sec = _msec = 0
		tmp = re.search('_(\d{2})_(\d{2})_(\d{2})(\d{3})', time_str)
		if tmp:
			_hours = int(tmp.group(1))
			_min = int(tmp.group(2))
			_sec = int(tmp.group(3))
			_msec = int(tmp.group(4))
		return ((_hours*60+_min)*60+_sec)*1000+_msec

	def humanTime(self):
		tm = self.time
		_hours = tm/(60*60*1000)
		tm = tm%(60*60*1000)
		_min = tm/(60*1000)
		tm = tm%(60*1000)
		_sec = tm/1000
		_msec = tm%1000
		return (_hours, _min, _sec, _msec)

	def humanTimeStr(self):
		return '%02d:%02d:%02d:%03d'%self.humanTime()

	def __str__(self):
		return 'cChapter(%s, "%s")'%(self.humanTimeStr(), self.title)

	def dump(self, mode='string'):
		if mode=='string':
			key = self.humanTimeStr()
			return '%s: %s'%(key, self.title.rjust(40-len(key)))
		elif mode=='dict':
			return [self.time, self.title]


class MediaInformer:
	def __init__(self, ffmpeg_path='ffmpeg', mkvtoolnix_path='', mediainfo_path='mediainfo', atomicParsley_path='AtomicParsley', artwork_path='.'):
		self.__ffmpeg_path = ffmpeg_path
		self.__mkvtoolnix_path = mkvtoolnix_path
		self.__mediainfo_path = mediainfo_path
		self.__atomicParsley_path = atomicParsley_path
		self.__map_stream_separated_symbol = None
		self.artwork_path = artwork_path

	def __stringToNumber(self, prm):
		if prm.find(' ')>-1:
			prm = prm[:prm.find(' ')]
		if prm.find('.')>-1:
			return float(prm)
		return int(prm)

	def __mediaDuration(self, filename):
		rv = None
		duration_re_compiled = re.compile('Duration:\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})')
		cmd = [self.__ffmpeg_path, '-i', filename]
		p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
		while True:
			retcode = p.poll()
			line = p.stdout.readline()
			if retcode is not None and len(line)==0:
				break
			duration_re =  duration_re_compiled.search(line)
			if duration_re:
				groups = duration_re.groups()
				hours = int(groups[0])
				mins = int(groups[1])
				secs = int(groups[2])
				ms = float(groups[3])
				rv = (hours*60.0 + mins)*60.0 + secs + ms/100
		return rv


	def fileInfoUsingFFMPEG(self, filename):
		'''
			Stream #0.0: Video: msmpeg4, yuv420p, 512x384, 23.98 tbr, 23.98 tbn, 23.98 tbc
			Stream #0.0(und): Video: h264 (High), yuv420p, 1280x720 [PAR 1:1 DAR 16:9], 1346 kb/s, 25.46 fps, 24 tbr, 1001 tbn, 2002 tbc
			Stream #0.2(jpn): Audio: aac, 48000 Hz, stereo, s16
			Stream #0.1(rus): Audio: aac, 48000 Hz, stereo, s16 (default)
			Stream #0.4(rus): Subtitle: ass
	    	Stream #0.0[0x1011]: Video: h264 (High), yuv420p, 1920x1080 [PAR 1:1 DAR 16:9], 23.98 fps, 23.98 tbr, 90k tbn, 47.95 tbc
    		Stream #0.1[0x1100](rus): Audio: dca (DTS), 48000 Hz, 5.1, s16, 768 kb/s
    		Stream #0.3[0x1102](rus): Audio: ac3, 48000 Hz, stereo, s16, 192 kb/s
	    	Stream #0.4[0x1103](jpn): Audio: dca (DTS-HD MA), 48000 Hz, 7 channels (FL|FR|FC|LFE|BC|SL|SR), s16, 1536 kb/s
			Stream #0.5[0x1104](jpn): Audio: truehd, 48000 Hz, 7 channels (FL|FR|FC|LFE|BC|SL|SR), s32
			Stream #0.6[0x1104]: Audio: ac3, 48000 Hz, 5.1, s16, 640 kb/s
			Stream #0:1[0x1100](rus): Audio: dts (DTS) ([130][0][0][0] / 0x0082), 48000 Hz, 5.1(side), s16, 768 kb/s
    	'''
		rv = cMediaInfo('ffmpeg', filename)
		#rv['filename'] = filename
		#rv['informer'] = 'ffmpeg'
		searchString = 'Stream #'
		streams = []
		cmd = [self.__ffmpeg_path, '-i', filename]
		#p = os.popen(self.__ffmpeg_path + ' -i \"%s\" 2>&1'%filename)
		p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
		streamTypes = ['Video:', 'Audio:', 'Subtitle:']
		while True:
			retcode = p.poll()
			line = p.stdout.readline()
			if line.find(searchString)>-1:
				l = line[line.find(searchString)+len(searchString):-1]
				tp = -1
				for i in range(len(streamTypes)):
					_type = streamTypes[i] 
					pos = l .find(_type)
					if pos>0:
						tp = i
						name =  l[:pos]
						l = l[pos+len(_type):]
						break

				name = name[:name.rfind(':')]
				name = re.sub(r'\[[^\]]*\]', '', name)
				lng = None
				i = name.find('(')
				if i>0:
					lng = name[i+1:name.find(')')]
					name = name[:i]

				prms = {}
				if tp == 0: #'Video':
					info = l.split(', ')
					prms['codec'] = info[0].strip()
					prms['colorFormat'] = info[1]
					res = info[2]
					prms['resolution'] = res
					w = res[:res.find('x')]
					res = res[len(w)+1:]
					if res.find(' ')>-1:
						res = res[:res.find(' ')]
					h = res
					prms['width'] = self.__stringToNumber(w)
					prms['height'] = self.__stringToNumber(h)

					if prms['codec']=='mjpeg':
						tp = 3
				
					#if len(prms['codec']>4) and prms['codec'][:4]=='h264':
					#	prms['bitrate'] = self.__stringToNumber(info[3])
					#	prms['fps'] = self.__stringToNumber(info[4])
				elif tp == 1: # 'Audio':
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
				elif tp == 2: #  == 'Subtitle':
					info = l.split(', ')
					prms['codec'] = info[0]
				else:
					#continue
					pass

				#streams.append([tp, name, lng, prms, ])
				if tp in range(4):
					streams.append(cStream(tp, name, lng, prms))
			if retcode is not None and len(line)==0:
				break
		i = len(streams)
		while i>0:
			if streams[i-1].type<>3:# or streams[i-1].params['codec']!='mjpeg':
				break
			i = i-1
		if i>0 and i<>len(streams):
			streams = streams[:i]
		#p.close()
		#rv['streams'] = streams
		rv.streams = streams
		return rv

	def mapStreamSeparatedSymbol(self, filename=None):
		if self.__map_stream_separated_symbol!=None:
			return self.__map_stream_separated_symbol

		if filename!=None:
			searchString = 'Stream #'
			#p = os.popen(self.__ffmpeg_path + ' -i "%s" 2>&1'%filename)
			cmd = [self.__ffmpeg_path, '-i', filename]
			p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
			rv = '+'
			while True:
				retcode = p.poll()
				line = p.stdout.readline()
				tmp = re.search('^\s+Stream\s+#0(.)\d+', line)
				if tmp:
					rv = tmp.group(1)
					break
				if retcode is not None and len(line)==0:
					break
			if rv=='+': rv = ':'
			self.__map_stream_separated_symbol = rv
		return self.__map_stream_separated_symbol

	def fileInfoUsingMKV(self, filename):
		def mkvInfoKeyValue(line):
			tmp = line.split(':')
			if len(tmp)==1:
				return (tmp[0].strip(), None)
			return (tmp[0].strip(), ':'.join(tmp[1:]).strip())


		ffmpegMapSeparatedSymbol = self.mapStreamSeparatedSymbol(filename)
		#rv = {}
		#rv['filename'] = filename
		#rv['informer'] = 'mkvinfo'
		rv = cMediaInfo('mkvinfo', filename)
		streams = []
		inTrackSegment = False
		streamType = None
		trackID = None
		lang = None
		prms = {}
		trackNumber = 0
		#p = os.popen(self.__mkvtoolnix_path + 'mkvinfo "%s" 2>&1'%filename)
		cmd = [self.__mkvtoolnix_path + 'mkvinfo', filename]
		p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
		while True:
			retcode = p.poll()
			line = p.stdout.readline()
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
						#streams.append([streamType, trackID, lang, prms, ])
						streams.append(cStream(streamType, trackID, lang, prms))
						streamType = None
						trackID = None
						lang = None
						prms = {}
				if inTrackSegment:
					(key, val) =  mkvInfoKeyValue(tmp)
					if key=='Track number':
						#trackID = '0.%d'%(int(val)-1)
						trackID = '0%s%d'%(ffmpegMapSeparatedSymbol, trackNumber)
						trackNumber = trackNumber+1
						r =  re.compile('mkvextract:.*(\d+)').search(val)
						if r:
							val = r.groups()[0]
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

			if retcode is not None and len(line)==0:
				break
		if streamType!=None:
			if lang==None:
				lang = 'und'
			#streams.append([streamType, trackID, lang, prms, ])
			streams.append(cStream(streamType, trackID, lang, prms))
		#rv['streams'] = streams
		rv.streams = streams
		return rv


	def fileInfoUsingMediaInfo(self, filename):
		rv = cMediaInfo('mediainfo', filename)
		curr_el = {'trackID_int': -1, 'streams': [], 'global': {}, 'chapters': [], 'track_block':-1}

		def start_element(name, attrs):
			curr_el['name'] = r'%s'%name.encode('utf-8')
			curr_el['attrs'] = attrs
			curr_el['data'] = ''
			if name=='track':
				if attrs.has_key('type'):
					#print attrs['type']
					if attrs['type']=='General':
						curr_el['track_block']=0
					elif attrs['type']=='Video' or attrs['type']=='Audio' or attrs['type']=='Text' or attrs['type']=='Image':
						curr_el['track_block']=1
						curr_el['trackID_int'] += 1
						track_type = -1
						if attrs['type']=='Video':
							track_type = 0
						if attrs['type']=='Audio':
							track_type = 1
						if attrs['type']=='Text':
							track_type = 2
						if attrs['type']=='Image':
							track_type = 3
						tid = '0%s%d'%(self.mapStreamSeparatedSymbol(filename), curr_el['trackID_int'])
						stream = cStream(track_type, tid, None, {})
						'''
						stream.append(track_type)
						stream.append('0%s%d'%(self.mapStreamSeparatedSymbol(filename), curr_el['trackID_int']))
						stream.append(None)
						stream.append({})
						'''
						curr_el['streams'].append(stream)
					elif attrs['type']=='Menu':
						curr_el['track_block']=2
					else:
						''' Missed block name '''
						curr_el['track_block']=-1

		def end_element(name):
			if len(curr_el['name']):
				#print curr_el['name'], curr_el['attrs'],curr_el['data']
				if len(curr_el['data']):
					if curr_el['track_block']==0:
						curr_el['global'][curr_el['name']] = r'%s'%curr_el['data'].encode('utf-8')
					elif curr_el['track_block']==1:
						curr_el['streams'][-1].params[curr_el['name']] = r'%s'%curr_el['data'].encode('utf-8')
						#curr_el['streams'][-1][-1][curr_el['name']] = r'%s'%curr_el['data'].encode('utf-8')
					elif curr_el['track_block']==2:
						time = curr_el['name']
						title = r'%s'%curr_el['data'].encode('utf-8')
						#print title, time
						curr_el['chapters'].append(cChapter(time, title))
						#curr_el['chapters'][curr_el['name']] = r'%s'%curr_el['data'].encode('utf-8')
			curr_el['name'] = ''
			curr_el['attrs'] = ''
			curr_el['data'] = ''
		def char_data(data):
			#print 'Character data:', repr(data)
			curr_el['data'] = curr_el['data'] + data

 	 	'''
			input: video file name
			output:
				{
					'informer': <informer app>
					'filename': filename
					'streams': 
						[
							[
								streamType,			// 0 - video, 1 - audio, 2 - subs
								trackID,			// ffmpeg track id ('0:0', '0:1')
								lang,				// language (3 chars)
								params = {}			// additional params (codec, width, height, dwidth, dheight ...)
							],
							...	
						]
					'tags': {
						'<tag_name>': '<value>',
						...
					}
				}
		'''

		#print self.__mediainfo_path + ' "%s" --Output=XML'%filename
		#os.environ['PYTHONIOENCODING'] = 'utf-8'
		#p = os.popen(self.__mediainfo_path + ' "%s" --Output=XML'%filename)
		cmd = [self.__mediainfo_path, filename, '--Output=XML']
		p = Popen(cmd, stdout=PIPE)
		data = ''
		while True:
			retcode = p.poll()
			line = p.stdout.readline()
			data = data + line
			if retcode is not None and len(line)==0:
				break

		#print '---start---'
		#print data
		#print '---end---'

		#import chardet
		#print chardet.detect(data)['encoding']
		#sys.exit()

		parser = xml.parsers.expat.ParserCreate()
		parser.StartElementHandler = start_element
		parser.EndElementHandler = end_element
		parser.CharacterDataHandler = char_data
		try:
			import chardet
			parser.Parse(unicode(data, chardet.detect(data)['encoding']).encode('utf-8'), 1)
		except Exception, e:
			return rv

		track_id = 0
		# convert int  values and like '4353 (0x1101)' or return string
		cnvrtToInt = lambda x: x.isdigit() and int(x) or x.split(' ')[0].isdigit() and int(x.split(' ')[0]) or x
		for stream in sorted(curr_el['streams'], key=lambda s: cnvrtToInt(s.params['ID'])):
			#fix track id's
			if stream.params.has_key('ID'):
				stream.trackID = '0%s%d'%(self.mapStreamSeparatedSymbol(filename), track_id)
			track_id += 1

			if stream.params.has_key('Language') and LANGUAGES_DICT.has_key(stream.params['Language']):
				stream.language = LANGUAGES_DICT[stream.params['Language']]


			if stream.type==0 and stream.params.has_key('Display_aspect_ratio'):
				try:
					width = int(stream.params['Width'].replace('pixels', '').replace(' ', ''))
					height = int(stream.params['Height'].replace('pixels', '').replace(' ', ''))
					display_aspect_ratio = stream.params['Display_aspect_ratio']
					if display_aspect_ratio.find(':')==-1:
						drx = float(display_aspect_ratio)
						dry = 1.0
					else:
						drx = float(stream.params['Display_aspect_ratio'][:stream.params['Display_aspect_ratio'].index(':')])
						dry = float(stream.params['Display_aspect_ratio'][stream.params['Display_aspect_ratio'].index(':')+1:])
					#print width, height, drx, dry
					stream.params['width'] = width
					stream.params['height'] = height
					if math.fabs(float(drx)/float(dry)-float(width)/float(height))>.1:
						stream.params['dheight'] = height
						stream.params['dwidth'] = height*drx/dry
				except Exception, e:
					pass
					#raise

		rv.streams = curr_el['streams']
		rv.general = curr_el['global']
		rv.chapters = curr_el['chapters']
		#rv['streams'] = curr_el['streams']
		#rv['global'] = curr_el['global']

		return rv


	def fileInfo(self, filename):
		'''
			input: video file name
			output:
				{
					'informer': <informer app>
					'filename': filename
					'streams': 
						[
							[
								streamType,			// 0 - video, 1 - audio, 2 - subs, 3 - image
								trackID,			// ffmpeg track id ('0:0', '0:1')
								lang,				// language (3 chars)
								params = {}			// additional params (codec, width, height, dwidth, dheight ...)
							],
							...	
						] 
					'tags': {
						'<tag_name>': '<value>',
						...
					}
				}
		'''

		rv = cMediaInfo('error', filename)
		tmp, ext = os.path.splitext(filename)
		ext = ext.lower()
		if ext=='.ass' or ext=='.srt' or ext=='.ttxt' or ext=='.ssa':
			rv.informer = 'none'
			rv.stream_add(cStream(2, '0%s0'%self.mapStreamSeparatedSymbol(filename), None, {'codec': ext[1:], 'encoding': fileCoding.file_encoding(filename)}))
		else:
			rv = self.fileInfoUsingMediaInfo(filename)
			if isMatroshkaMedia(filename):
				tmp = self.fileInfoUsingMKV(filename)
				if len(rv.streams)==len(tmp.streams):
					for stream in rv.streams:
						for i in range(len(tmp.streams)):
							if stream.trackID==tmp.streams[i].trackID and stream.type==tmp.streams[i].type and tmp.streams[i].params.has_key('mkvinfo_trackNumber'):
								stream.params['mkvinfo_trackNumber'] = tmp.streams[i].params['mkvinfo_trackNumber']

			if len(rv.streams)==0:
				rv = self.fileInfoUsingFFMPEG(filename)

		try:
			rv.general['mediaDuration'] = self.__mediaDuration(filename)
		except Exception, e:
			pass
			#raise e

		if ext=='.mp4' or ext=='.m4v':
			rv.tags = self.__readTags(filename)

		return rv


	def __readTags(self, filename):
		rv = {}
		#p = os.popen(self.__atomicParsley_path + ' \"%s\" -t'%filename)
		cmd = [self.__atomicParsley_path, filename, '-t']
		p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
		key = None
		val = ''
		while True:
			retcode = p.poll()
			line = p.stdout.readline()
			srch = re.compile('Atom \"(.{4,5})\"').search(line)
			if srch!=None:
				if key!=None:
					rv[key] = val[:-1]
				val = line[line.find(':')+2:]
				key = srch.groups()[0]
				if key=='----':
					srch = re.compile('\"\s\[(.+)\]').search(line)
					if srch!=None:
						key = srch.groups()[0]
			else:
				val += line
			if retcode is not None and len(line)==0 and len(line)==0:
				break
		if key!=None:
			rv[key] = val[:-1]

		convert_dictionary = {
		'©art': 'artist',
		'©ART': 'artist',
		'©nam': 'title',
		'©alb': 'album',
		'©gen': 'genre',
		'gnre': 'genre',
		#'': 'comment',
		'©day': 'year',
		'©lyr': 'lyrics',
		'©wrt': 'composer',
		'cprt': 'copyright',
		'©grp': 'grouping',
		'covr': 'artwork',
		'tmpo': 'bpm',
		'aART': 'albumArtist',
		'cpil': 'compilation',
		'hdvd': 'hdvideo',
		'trkn': 'tracknum', 
		'disk': 'disk',
		#'rtng': 'advisory',
		'stik': 'stik',
		'desc': 'description',
		'rtng': 'Rating',
		'ldes': 'longdesc',
		'sdes': 'storedesc',
		'tvnn': 'TVNetwork',
		'tvsh': 'TVShowName',
		'tven': 'TVEpisode',
		'tvsn': 'TVSeasonNum',
		'tves': 'TVEpisodeNum',
		#'': 'podcastFlag',
		'catg': 'category',
		'keyw': 'keyword',
		'purl': 'podcastURL',
		'egid': 'podcastGUID ',
		'purd': 'purchaseDate',
		'©too': 'encodingTool',
		'©enc': 'encodedBy',
		'apID': 'apID',
		'cnID': 'cnID',
		#'': 'geID',
		#'': 'xId',
		'pgap': 'gapless',
		#'': 'sortOrder',
		}

		ap_params = {}
		for k in rv.keys():
			if convert_dictionary.has_key(k):
				if k=='trkn' or k=='disk':
					ap_params[convert_dictionary[k]] = rv[k].replace(' of ', '/')
				else:
					ap_params[convert_dictionary[k]] = rv[k]
			else:
				ap_params[k] = rv[k]

		if ap_params.has_key('artwork'):
			name = '.'.join(os.path.basename(filename).split('.')[:-1])
			fname = '%s/%s'%(self.artwork_path, name)
			#p = os.popen(self.__atomicParsley_path + ' \"%s\" -e \"%s\"'%(filename, fname))
			cmd = [self.__atomicParsley_path, filename, '-e', fname]
			p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
			while True:
				retcode = p.poll()
				line = p.stdout.readline()
				if line.find('Extracted artwork to file:')!=-1:
					ap_params['artwork'] = line[line.find(':')+1:].strip()
					p.kill()
					break
				if retcode is not None and len(line)==0:
					break

		return ap_params


if __name__=='__main__':
	mi = MediaInformer(ffmpeg_path, mkvtoolnix_path, mediainfo_path, AtomicParsley_path, os.getenv('HOME')+'/Desktop')
	for arg in sys.argv[1:]:
		fi = mi.fileInfo(arg)
		print fi.dump()

