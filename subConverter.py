#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import glob
import sys
import os
import string

STTNGS = {
'ASSremoveItems' : ('EdKara', 'TVLpaint', 'SerialMainTitle', 'Kar_OP_1', 'Kar_OP_2', 'Kar_OP_3', 'Kar_OP_4', 	'Kar_ED_1', 'Kar_ED_2', 'Kar_ED_3', 'Kar_ED_4', 'Kar_ED_5', 'Kar_ED_6', '# WORKING OP RO', 'Ending2', 	'EPtv_txt1', 'EPtv_txt2', 'BackComment',
	'Song1' ),

'subStyleColors' : {
	"prew" : "d9a1afi",
	"end" : "d37f63i",
	"rus_op" : "8ad3a1i",
	"rus_ed" : "8ad3a1i",
	"eng_op" : "9292e6i",
	"eng_ed" : "9292e6i"
	},

'subReplace' : {
	unicode("На", 'utf-8'): {
			"text": unicode("<i><font color=\"#b9d4b5\">На</font><font color=\"#846546\">зад обернувшись, смотрю пред собою:\n\"Кто там стоит?\"</font></i>", 'utf-8'),
			"style": "Song1",
			"duration": 470
		},
	unicode("Когтями", 'utf-8'): {
			"text": unicode("Когтями на части всю тьму разорвало...", 'utf-8'),
			"style": "Song1",
		},
	unicode("Когда", 'utf-8'): {
			"text": unicode("Когда обернётся дождь крови рекой,\nна горло мое вдруг прольется потоком...", 'utf-8'),
			"style": "Song1",
		},
	unicode("Не будет", 'utf-8'): {
			"text": unicode("Не будет впредь места на целой", 'utf-8'),
			"style": "Song1",
		},
	unicode("Земле, куда ты вернуться бы смог.", 'utf-8'): {
			"text": unicode("Земле, куда ты вернуться бы смог.", 'utf-8'),
			"style": "Song1",
		},
	unicode("Иди вслед за пальцем,", 'utf-8'): {
			"text": unicode("Иди вслед за пальцем, за пальцем моим.\nЯ тебя уведу за собою в тот лес,..", 'utf-8'),
			"style": "Song1",
		},
	unicode("...где цикады стрекочут", 'utf-8'): {
			"text": unicode("...где цикады стрекочут во тьме.\nНо назад ты уже не вернёшься...", 'utf-8'),
			"style": "Song1",
		},
	},
}

class subConverter:
	def __init__(self, STTNGS={}):
		self.__STNGS = STTNGS

	def timesrt(self, stamp):
		if len(stamp)==12:
			return stamp
		return "0%s0" % (stamp.replace('.', ','))
	
	def time2int(self, stamp):
		if stamp==None:
			return None
		tmp = stamp.split(':')
		ms = int(tmp[2].replace('.','').replace(',',''));
		return 60*1000*(int(tmp[0])*60+int(tmp[1]))+ms

	def int2time(self, i):
		(i, ms) = divmod(i, 1000)
		(i, s) = divmod(i, 60)
		(h, m) = divmod(i, 60)
		return '%02d:%02d:%02d,%02d0'%(h,m,s,ms/10)
	
	def mergeSubs(self, sub, add, anywayNeedSpace):
		tmp = ''
		if len(unicode(add,'utf-8'))>1 or anywayNeedSpace:
			tmp = '\n'
		return '%s%s%s'%(sub,tmp,add)

	def __insert(self, arr, val):
		if len(arr)==0:
			arr.append(val)
		elif len(arr)==1:
			if self.time2int(val[1])>self.time2int(arr[0][1]):
				arr.append(val)
			else:
				arr.insert(0, val)
		else:
			s = ''
			x = self.time2int(val[1])
			if x>=self.time2int(arr[-1][1]):
				arr.append(val)
			else:
				l = len(arr)/2+len(arr)%2
				i = l
				while l>1:
					s = '%s %d'%(s,i)
					l = l/2 + l%2
					if x>self.time2int(arr[i][1]):
						if (i+l)>=len(arr): l=len(arr)-i-1
						i += l
					else:
						i -= l
				if x>self.time2int(arr[i][1]): i+=1
				if i<0:
					i=0
				
				# fix position
				while i>0:
					if x<self.time2int(arr[i][1]): i-=1
					else: break
				while i<len(arr):
					if x>self.time2int(arr[i][1]): i+=1
					else: break
				arr.insert(i, val)
	
	def postProcessing(self, s):
		arr = s.strip().split('\n')
		i=0
		c=0
		x1=0 
		while i<len(arr):
			if len(unicode(arr[i],'utf-8'))==1:
				c+=1
				x1 = i-c+1
			else:
				if c>4:
					s2 = ''
					for j in range(x1, x1+c):
						s2 += arr[j]
					tmp = []
					for j in range(x1):
						tmp.append(arr[j])
					tmp.append(s2)
					for j in range(x1+c, len(arr)):
						tmp.append(arr[j])
					arr = tmp					
				i-=c
				c=0
			i+=1
		if c>4:
			s2 = ''
			for j in range(x1, x1+c):
				s2 += arr[j]
			tmp = []
			for j in range(x1):
				tmp.append(arr[j])
			tmp.append(s2)
			for j in range(x1+c, len(arr)):
				tmp.append(arr[j])
			arr = tmp					
		return '\n'.join(arr)

	def writeOut(self, fname_srt, lines):
		'''
				write with merge by timing
		'''

		num = 1
		s = ''
		last = (None, None)
		last_elems = None
		merged = False
		minTime = None
		fo = open(fname_srt,'w')
		for l in lines:
			curr = ( l[1], l[2] )
			if self.time2int(curr[0])<self.time2int(last[1]):
				newStop = self.time2int(last[0]) + 4*(self.time2int(last[1])-self.time2int(last[0]))/5
				if self.time2int(curr[0])>=newStop:
					newStop = self.time2int(curr[0])+(self.time2int(last[1])-self.time2int(curr[0]))/2
					minTime = self.int2time(newStop+20)
					last = (last[0], self.int2time(newStop))
					curr = (minTime, curr[1])
					if self.time2int(curr[0])>self.time2int(curr[1]):
						curr = (curr[1], curr[0])
					if s!='':
						fo.write('%d\n%s --> %s\n%s\n\n'%(num, last[0], last[1], self.postProcessing(s)))
						num += 1
					merged = False
					s=l[3]
				else:
					s = self.mergeSubs(s,l[3], l[0]!=last_elems[0])
					if self.time2int(curr[0])>self.time2int(last[0]):
						curr = (last[0], curr[1])
					if self.time2int(curr[1])<self.time2int(last[1]):
						curr = (curr[0], last[1])
					if minTime != None:
						curr = (minTime, curr[1])
					merged = True
			else:
				if s!='':
					fo.write('%d\n%s --> %s\n%s\n\n'%(num, last[0], last[1], self.postProcessing(s)))
					num += 1
				minTime = None
				merged = False
				s=l[3]
			last = curr
			last_elems = l

		if s!='':
			fo.write('%d\n%s --> %s\n%s\n\n'%(num, last[0], last[1], self.postProcessing(s)))

		fo.close()

	def convertL2srtFormat(self, l):
		txt = l[3]
		for style in l[4]:
			if style[0][0]=='#' and string.upper(style[0][1:])!='FFFFFF':
				txt = '<font color="%s">%s</font>'%(style[0], txt)
			if style[0][0]=='i':
				txt = '<i>%s</i>'%(txt)
			if style[0][0]=='u':
				txt = '<u>%s</u>'%(txt)
			if style[0][0]=='<':
				txt = ' &lt;%s&gt;'%(txt)
		return (l[0], l[1], l[2], txt, l[4])

	def groupByTime(self, lines):
		last = (None, None)
		subs = []
		utterance = []
		for l in lines:
			curr = ( l[1], l[2] )
			if self.time2int(curr[0])<self.time2int(last[1]) or last[0]==None:
				utterance.append(l) 
				if self.time2int(curr[1])<self.time2int(last[1]) and last[1]!=None:
					curr = (curr[0], last[1])
			elif len(utterance)>0:
				subs.append(utterance)
				utterance = [l,]
			last = curr

		if len(utterance)>0:
			subs.append(utterance)
		return subs

	def writeOut2srt(self, fname_srt, lines):
		'''
				write with points at new line
		'''
		s = ''
		subs = self.groupByTime(lines)
		for i in subs:
			for j in range(len(i)):
				i[j] = self.convertL2srtFormat(i[j])

		num = 1
		fo = open(fname_srt,'w')
		emptyLine = '<font color="#383838">.</font>'
		for i in subs:
			maxLines = 0
			minTm = i[0][1]
			maxTm = minTm
			for l in i:
				x=0
				for j in i:
					 if  (self.time2int(l[1])>=self.time2int(j[1])) and (self.time2int(l[1])<self.time2int(j[2])):
						x+=1
				if maxLines<x: maxLines=x
				if self.time2int(l[1])<self.time2int(minTm): minTm = l[1]
				if self.time2int(l[2])>self.time2int(maxTm): maxTm = l[2]
			lastTm = minTm
			_prew = []
			while self.time2int(lastTm)<self.time2int(maxTm):
				linesByTime = []
				tm = None
				for j in i:
					if (self.time2int(j[1])>self.time2int(lastTm)) and (self.time2int(j[1])<self.time2int(tm) or tm==None):
						tm = j[1]
					if (self.time2int(j[2])>self.time2int(lastTm)) and (self.time2int(j[2])<self.time2int(tm) or tm==None):
						tm = j[2]
				for j in i:
					if  ((self.time2int(lastTm)>=self.time2int(j[1])) and (self.time2int(lastTm)<self.time2int(j[2]))):
						linesByTime.append(j)

				s = []
				_now = []
				for j in range(maxLines):
					s.append(emptyLine)
					_now.append(None)
				tmp = []
				for l in linesByTime: tmp.append(l)
				for k in range(len(_prew)):
					for n in range(len(tmp)):
						if tmp[n]==_prew[k]:
							s[k] = tmp[n][3]
							_now[k] = tmp[n]
							tmp.remove(tmp[n])
							break
				for l in tmp:
					j=0
					while s[j]!=emptyLine:
						j+=1
					s[j] = l[3]
					_now[j] = l
				_prew = _now
				while s[0]==emptyLine:
					s = s[1:]

				#print "%s\t%s\t%s"%(lastTm, tm, " \t ".join(s))
				if s!='':
					if self.time2int(lastTm)<self.time2int(tm):
						fo.write('%d\n%s --> %s\n%s\n\n'%(num, lastTm, tm, self.postProcessing("\n".join(s))) )
						num += 1
				#lastTm = self.int2time(self.time2int(tm)+20)
				lastTm = tm

		fo.close()

	def readAss(self, fname_ass):
		fi = open(fname_ass)
		block = 0
		lines = []
		black_list = ()
		if self.__STNGS.has_key('ASSremoveItems'):
			black_list = self.__STNGS['ASSremoveItems']
		subReplace = {}
		if self.__STNGS.has_key('subReplace'):
			subReplace = self.__STNGS['subReplace']
		lastVal = None
		styles = {}
		for line in fi:
			if block==2:
				elems = line.split(',')
				t =  re.compile('Style:\s*([^,]+)').match(elems[0])
				if t:
					sName = t.groups()[0]
					t =  re.compile('\&(H[0-9a-fA-F]{2})([0-9a-fA-F]{6})').match(elems[3])
					if t:
						col = t.groups()[1]
						styles[sName] = (col,)
			if block==3:
				#print line
				if line[:8] == 'alogue: ':
					line = 'Di%s'%line
				if line[:10] == 'Dialogue: ':
					line = line[8:]
					elems = line.split(',')
					linetext = ",".join(elems[9:])
					linetext = unicode( linetext, "utf-8" )
					linetext = linetext.replace('\\n','\\N');
					linetext = linetext.replace('\\N','\n');
					linetext = re.sub(r'\{\\[^\}]*\}', '', linetext)
					linetext = re.sub(r'([lmb](\s\-{0,1}\d+){2,6}\s{0,1}){2,}', '', linetext)	# m 0 0 l 0 150 l 250 150 l 250 0
					linetext = re.sub(r'm\s\-{0,1}\d+\s+\-{0,1}\d+\s+s(\s+\-{0,1}\d+){14}\s+c', '', linetext)	# m 5 0 s 95 0 100 5 100 95 95 100 5 100 0 95 0 5 c
					#linetext = re.sub(r'\{[^\}]*\}', '', linetext)		# remove from subs {xxxx}

					blackCheck = True
					subEnd = self.timesrt(elems[2])
					if subReplace.has_key(linetext.strip()):
						v = subReplace[linetext.strip()]
						if (not v.has_key('style')) or (v.has_key('style') and v['style']==elems[3].strip()):
							linetext = v['text']
							if v.has_key('duration'):
								subDuration = v['duration']
								subEnd = self.int2time(self.time2int(self.timesrt(elems[1]))+subDuration)
							blackCheck = False

					if blackCheck:
						bl = False
						for style in black_list:
							if style==elems[3]:
								bl = True
								break
						if bl:
							continue

					while linetext.find('\n\n')>0:
						linetext = linetext.replace('\n\n','\n');
					linetext = linetext.strip().encode('utf-8')
					#print len(unicode(linetext,'utf-8')),linetext
					if len(linetext)>0:
						_style = elems[3].strip()
						if _style[0]=='*': _style= _style[1:]
						val = (_style, self.timesrt(elems[1]), subEnd, linetext, [])
						self.__insert(lines, val)
						lastVal = val

			line = line.strip()
			if '[Script Info]' == line:
				block = 1
			if ('[V4+ Styles]' == line) or ('[V4 Styles]' == line):
				block = 2
			if '[Events]' == line:
				block = 3
			#if re.compile('Format\: Layer, Start, End').match(line):
			#	start = True;
			#if re.compile('\[Events\]').match(line):
			#	start = True;
		fi.close()

		c = None
		needFontTag = False;
		for l in lines:
			if styles.has_key(l[0]):
				if c!=None:
					if c != styles[l[0]]:
						needFontTag = True
						break
				c = styles[l[0]]
			if self.__STNGS.has_key('subStyleColors'):
				if self.__STNGS['subStyleColors'].has_key(styles[l[0]]):
					if string.upper(self.__STNGS['subStyleColors'][styles[l[0]]])!='FFFFFF':
						needFontTag = True
						break

		if needFontTag:
			for i in range(len(lines)):
				l = lines[i]
				if self.__STNGS.has_key('subStyleColors'):
					if self.__STNGS['subStyleColors'].has_key(l[0]):
						tmp = False
						style = self.__STNGS['subStyleColors'][l[0]].encode( "utf-8" )
							#MP4Box convert subs looks like "<i><font color="xxxxxx">qwerty</font></i>"
						lines[i][4].append(("#%s"%style[:6],))
						if len(style)>6:
							if style[6]=='<':
								lines[i][4].insert(0, (string.lower(style[6]), ))
							else:
								lines[i][4].append((string.lower(style[6]), ))
						continue
				if styles.has_key(l[0]):
					lines[i][4].append(("#%s"%styles[l[0]][0],))
						#lines[i] = ( l[0], l[1], l[2], '<font color="#%s">%s</font>'%(styles[l[0]][0],l[3]) )
		

		return lines

	def readSrt(self, fname_srt):
		fi = open(fname_srt)
		idx = None
		tm = None
		txt = None
		lastLineEmpty = True
		set = False
		lines = []
		for line in fi:
			line = line.strip()
			if len(line)>3 and line[:3]=='\xEF\xBB\xBF':
				line = line[3:]

			line = re.sub(r'\{\\[^\}]*\}', '', line)

			if len(line)!=0:
				if lastLineEmpty:
					try:
					    x = int(line)
					except:
						x = None
					if x!=None and txt!=None:
						ttt = tm.split('-->')
						if len(ttt)==2:
							tm1 = ttt[0].strip()
							tm2 = ttt[1].strip()
							val = ('', tm1, tm2, txt, [])
							self.__insert(lines, val)
							#print '%d\n-%s\n--%s'%(idx, tm, txt)
							#fo.write('%d\n%s\n%s\n\n'%(idx, tm, txt))
						idx = x
						tm = None
						txt = None
						set= True
					# first
					if idx==None and x!=None:
						idx = x
						set= True
				if not set:
					if tm==None:
						tm = line
					elif txt==None:
						txt = line
					else:
						txt += '\n%s'%line
				set= False
				lastLineEmpty = False
			else:
				lastLineEmpty = True

		if idx!=None and tm!=None and txt!=None:
			ttt = tm.split('-->')
			if len(ttt)==2:
				tm1 = ttt[0].strip()
				tm2 = ttt[1].strip()
				val = ('', ttt[0].strip(), ttt[1].strip(), txt, [])
				self.__insert(lines, val)
		fi.close()

		return lines
	
	def flexibleTiming(self, lines, t):
		"""
			Fixing times on subs
							  source        shuld be        source       shuld be    
			t have format [('0:22:03.58', '0:21:10.00'), ('0:02:28.69', '0:02:22.85')]
			
			for Serial Experiments Lain
				el01 = [('0:22:03.58', '0:21:10.00'), ('0:02:28.69', '0:02:22.85')]
				el02 = [('0:20:53.80', '0:20:03.90'), ('0:02:09.00', '0:02:05.00')]
				el03 = [('0:21:33.37', '0:20:42.10'), ('0:02:28.27', '0:02:23.85')]
				el04 = [('0:21:42.35', '0:20:50.70'), ('0:02:28.55', '0:02:24.10')]
				el05 = [('0:21:06.85', '0:20:13.70'), ('0:02:30.55', '0:02:23.17')]
				el06 = [('0:21:45.90', '0:20:53.50'), ('0:02:28.80', '0:02:23.80')]
				el07 = [('0:21:30.10', '0:20:37.80'), ('0:02:29.60', '0:02:23.80')]
				el08 = [('0:21:55.90', '0:21:02.10'), ('0:02:30.00', '0:02:23.45')]
				el09 = [('0:21:24.33', '0:20:32.80'), ('0:02:29.03', '0:02:23.95')]
				el10 = [('0:21:21.15', '0:20:28.60'), ('0:02:29.45', '0:02:23.00')]
				el11 = [('0:22:08.96', '0:21:14.35'), ('0:02:30.36', '0:02:23.00')]
				el12 = [('0:21:30.10', '0:20:38.00'), ('0:02:29.40', '0:02:23.30')]
				el13 = [('0:21:02.61', '0:20:36.00'), ('0:02:32.31', '0:02:50.95')]
		"""
		rv = []
		i = self.time2int(self.timesrt(t[0][0]))-self.time2int(self.timesrt(t[1][0]))
		o = self.time2int(self.timesrt(t[0][1]))-self.time2int(self.timesrt(t[1][1]))
		x1 = self.time2int(self.timesrt(t[1][0]))
		x2 = self.time2int(self.timesrt(t[1][1]))
		print i, o, self.int2time(i), self.int2time(o)
		for l in lines:
			t1 = self.int2time((self.time2int(l[1])-x1)*o/i+x2)
			t2 = self.int2time((self.time2int(l[2])-x1)*o/i+x2)
			val = l[0], t1, t2, l[3]
			rv.append(val)
		return rv

	def ass2srt(self, fname_ass, fname_srt, sttngs={}):
		lines = self.readAss(fname_ass)

		if sttngs.has_key('flexibleTime'):
			lines = self.flexibleTiming(lines, sttngs['flexibleTime'] )

		self.writeOut2srt(fname_srt, lines)
		return fname_srt

	def srt2srt(self, fname_srt1, fname_srt2=None, sttngs={}):
		tmp_fn = fname_srt2
		if fname_srt1==fname_srt2 or fname_srt2==None:
			tmp_fn = "%s.tmp"%fname_srt1

		lines = self.readSrt(fname_srt1)

		if sttngs.has_key('flexibleTime'):
			lines = self.flexibleTiming(lines, sttngs['flexibleTime'] )

		self.writeOut2srt(tmp_fn, lines)

		if fname_srt1==fname_srt2 or fname_srt2==None:
			cmd = 'mv "%s" "%s"'%(tmp_fn, fname_srt1)
			print cmd
			os.system(cmd)
		return fname_srt2

	def readAssStyles(self, fname_ass, styles={}):
		fi = open(fname_ass)
		block = 0
		for line in fi:
			if block==2:
				elems = line.split(',')
				t =  re.compile('Style:\s*([^,]+)').match(elems[0])
				if t:
					sName = t.groups()[0]
					t =  re.compile('\&(H[0-9a-fA-F]{2})([0-9a-fA-F]{6})').match(elems[3])
					if t:
						col = t.groups()[1]
						styles[sName] = (col,)

			line = line.strip()
			if '[Script Info]' == line:
				block = 1
			if ('[V4+ Styles]' == line) or ('[V4 Styles]' == line):
				block = 2
			if '[Events]' == line:
				block = 3
		fi.close()

		return styles



if __name__=='__main__':
	if len(sys.argv)==2:
		sc = subConverter(STTNGS)
		if sys.argv[1][-4:]=='.srt':
			sc.srt2srt(sys.argv[1])
		else:
			fname_srt = os.path.basename(re.compile('\\.ass$').sub('.srt', sys.argv[1]))
			print sys.argv[1], fname_srt
			sc.ass2srt(sys.argv[1], fname_srt)
	elif len(sys.argv)>2:
		if sys.argv[1]=='-styles':
			sc = subConverter(STTNGS)
			st = {}
			for i in range(2, len(sys.argv)):
				st = sc.readAssStyles(sys.argv[i], st)
			keys = st.keys()
			keys.sort()
			for key in keys:
				print key, '\t', st[key] 
			
	

	sss = '''{\\r\\fscx110\\fscy120\\fsp2\\t(400,550,\\1a&HFF&)}р{\\r\\fscx110\\fscy120\\fsp2\\t(100,250,\\1a&HFF&)}е{\\rfscx110\\fscy120\\fsp2\\t(350,500,\\1a&HFF&)}д{\\r\\fscx110\\fscy120\\fsp2\\t(350,500,\\1a&HFF&)}а{\\r\\fscx110\\fscy120\\fsp2\\t(500,650,\\1a&HFF&)}к{\\r\\fscx110\\fscy120\\fsp2\\t(600,750,\\1a&HFF&)}ц{\\fscx110\\fscy120\\fsp2\\t(250,400,\\1a&HFF&)}и{\\r\\fscx110\\fscy120\\fsp2\\t(0,150,\\1a&HFF&)}я: {\\r\\fscx110\\fscy120\\fsp2\\t(550,700,\\1a&HFF&)}n{\\r\\fscx110\\fscy120\\fsp2\\t(50,200,\\1a&HFF&)}e{\\r\\fscx110\\fscy120\\fsp2\\t(650,800,\\1a&HFF&)}u{\\r\\fscx110\\fscy120\\fsp2\\t(200,350,\\1a&HFF&)}t{\\r\\fscx110\\fscy120\\fsp2\\t(300,600,\\1a&HFF&)}r{\\r\\fscx110\\fscy120\\fsp2\\t(700,850,\\1a&HFF&)}a{\\r\\fscx110\\fscy120\\fsp2\\t(250,400,\\1a&HFF&)}l'''
	tmp = re.sub(r'\{\\[^\}]*\}', '', sss)
	print '\n-------------'
	print unicode(tmp, 'utf-8').encode('ascii', 'xmlcharrefreplace')
	
	linetext = '{\p1\fscx76.25\fscy97.5\frz328.141\pos(578,189)}m -105 68 l -91 39 l -77 68 l -80 68 l -84 59 l -98 59 l -102 68 m -73 68 l -73 39 l -64 39 b -54 39 -48 44 -48 54 b -48 65 -55 68 -64 68 m -32 68 l -45 39 l -41 39 l -32 61 l -22 39 l -19 39 m -18 68 b -21 68 -21 66 -21 62 b -22 60 -22 59 -20 56 b -17 51 -15 41 -10 36 b -9 34 -9 29 -7 26 l -9 25 l -4 16 b -5 16 -7 15 -6 14 b -5 13 -8 13 -9 13 b -12 11 -13 10 -13 6 b -11 4 -11 -2 -10 -6 b -10 -8 -7 -8 -5 -9 b -3 -10 -3 -11 -3 -12 b -3 -14 -5 -14 -7 -12 b -7 -14 -10 -12 -12 -13 b -10 -15 -9 -15 -8 -16 l -11 -16 b -9 -17 -7 -18 -7 -21 b -7 -24 -7 -26 -5 -28 b -4 -29 -1 -29 0 -27 l -1 -30 b 1 -28 3 -29 2 -26 b 4 -27 6 -26 7 -24 b 7 -27 10 -26 12 -28 b 10 -24 13 -24 14 -21 b 15 -18 14 -15 12 -13 b 19 -10 9 -8 14 -6 b 13 -6 11 -6 10 -7 b 12 -10 8 -10 7 -11 l 6 -14 b 5 -12 4 -11 2 -10 b 2 -9 5 -9 8 -8 b 15 -3 19 1 19 2 b 19 4 17 7 9 7 b 13 13 12 18 14 20 b 14 21 13 22 12 22 b 13 27 12 31 12 34 b 13 44 11 51 10 55 l 10 58 b 12 59 10 61 10 62 b 11 67 10 68 7 68 b 5 68 3 67 3 65 b 3 63 6 62 7 58 b 7 51 7 47 7 39 b 7 35 6 30 5 26 b 4 26 2 26 1 26 b -3 33 -4 37 -8 42 b -10 48 -11 50 -17 58 b -17 61 -16 63 -13 66 b -13 68 -16 68 -17 68 m 16 68 l 16 39 l 36 61 l 36 39 l 39 39 l 39 68 l 19 47 l 19 68 m 49 68 l 49 41 l 43 41 l 43 39 l 58 39 l 58 41 l 52 41 l 52 68 m 61 68 l 74 39 l 88 68 l 85 68 l 81 59 l 68 59 l 64 68 m 110 54 l 122 54 b 123 65 113 69 107 69 b 102 69 92 65 92 54 b 92 45 99 39 107 39 b 114 39 117 41 121 44 l 119 47 b 115 44 113 42 107 42 b 101 42 95 46 95 54 b 95 63 103 66 107 66 b 113 66 118 64 119 57 l 110 57 m 128 68 l 128 39 l 145 39 l 145 42 l 131 42 l 131 51 l 145 51 l 145 54 l 131 54 l 131 65 l 145 65 l 145 68 m -86 56 l -91 46 l -96 56 m -70 42 l -70 66 l -65 66 b -59 66 -50 63 -51 54 b -51 46 -57 42 -65 42 m 79 56 l 74 45 l 69 56 m -4 11 b -4 8 -5 6 -6 4 b -7 4 -9 8 -7 9 m 6 3 b 6 4 6 5 7 5 b 8 4 11 3 12 2 b 10 1 8 0 6 -2 {\p0}'
	linetext = re.sub(r'\{\\[^\}]*\}', '', linetext)
	linetext = re.sub(r'([lmb](\s\-{0,1}\d+){2,6}\s{0,1}){2,}', '', linetext)	# m 0 0 l 0 150 l 250 150 l 250 0
	linetext = re.sub(r'm\s\-{0,1}\d+\s+\-{0,1}\d+\s+s(\s+\-{0,1}\d+){14}\s+c', '', linetext)
	print "-%s-"%linetext


