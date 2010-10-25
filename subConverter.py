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
			"text": unicode("Назад обернувшись, смотрю пред собою:\n\"Кто там стоит?\"", 'utf-8'),
			"style": "Song1"
		},
	unicode("Когтями", 'utf-8'): {
			"text": unicode("Когтями на части всю тьму разорвало...", 'utf-8'),
			"style": "Song1"
		},
	unicode("Когда", 'utf-8'): {
			"text": unicode("Когда обернётся дождь крови рекой,\nна горло мое вдруг прольется потоком...", 'utf-8'),
			"style": "Song1"
		},
	unicode("Не будет", 'utf-8'): {
			"text": unicode("Не будет впредь места на целой", 'utf-8'),
			"style": "Song1"
		},
	unicode("Земле, куда ты вернуться бы смог.", 'utf-8'): {
			"text": unicode("Земле, куда ты вернуться бы смог.", 'utf-8'),
			"style": "Song1"
		},
	unicode("Иди вслед за пальцем,", 'utf-8'): {
			"text": unicode("Иди вслед за пальцем, за пальцем моим.\nЯ тебя уведу за собою в тот лес,..", 'utf-8'),
			"style": "Song1"
		},
	unicode("...где цикады стрекочут", 'utf-8'): {
			"text": unicode("...где цикады стрекочут во тьме.\nНо назад ты уже не вернёшься...", 'utf-8'),
			"style": "Song1"
		},
	},
}

class subConverter:
	def __init__(self, STTNGS={}):
		self.__STNGS = STTNGS

	def timesrt(self, stamp):
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
					linetext = re.sub(r'([lm]\s\-{0,1}\d+\s\-{0,1}\d+\s{0,1}){2,}', '', linetext)	# m 0 0 l 0 150 l 250 150 l 250 0
					linetext = re.sub(r'm\s\-{0,1}\d+\s+\-{0,1}\d+\s+s(\s+\-{0,1}\d+){14}\s+c', '', linetext)	# m 5 0 s 95 0 100 5 100 95 95 100 5 100 0 95 0 5 c
					#linetext = re.sub(r'\{[^\}]*\}', '', linetext)		# remove from subs {xxxx}

					blackCheck = True
					if subReplace.has_key(linetext.strip()):
						v = subReplace[linetext.strip()]
						if (not v.has_key('style')) or (v.has_key('style') and v['style']==elems[3].strip()):
							linetext = v['text']
							blackCheck = False

					if blackCheck:
						bl = False
						for style in black_list:
							if style==elems[3]:
								bl = True
								break
						if bl:
							continue

					'''
					# Ergo proxy  
					linetext = linetext.strip()
					bl = False
					for lt in ['EP', 'op', 'ed', 'and', 'save', 'me', 'could', 'stop', 'you', 'the', 'noise', 'I\'m', 'trying', 'to', 'get', 'some', 'rest', 'all', 'un', 'born', 'chi', 'cken', 'voi', 'ces', 'in', 'my', 'head', 'that']:
						if linetext==lt:
							bl = True
							break
					if bl:
						continue
					if linetext=='Come':
						linetext = 'Come and save me'
					if linetext=='Please':
						linetext = 'Please could you stop the noise I\'m trying to get some rest'
					if linetext=='From':
						linetext = 'From all the unborn chicken voices in my head'
					if linetext=='What\'s':
						linetext = 'What\'s that'
					if lastVal!=None:
						if linetext.encode('utf-8')==lastVal[3] and lastVal[0]=='EP_Title2':
							continue
					 '''

					while linetext.find('\n\n')>0:
						linetext = linetext.replace('\n\n','\n');
					linetext = linetext.strip().encode('utf-8')
					#print len(unicode(linetext,'utf-8')),linetext
					if len(linetext)>0:
						_style = elems[3].strip()
						if _style[0]=='*': _style= _style[1:]
						val = (_style, self.timesrt(elems[1]), self.timesrt(elems[2]), linetext, [])
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
			for key in st:
				print key, '\t', st[key] 
			
	

	sss = '''{\\r\\fscx110\\fscy120\\fsp2\\t(400,550,\\1a&HFF&)}р{\\r\\fscx110\\fscy120\\fsp2\\t(100,250,\\1a&HFF&)}е{\\rfscx110\\fscy120\\fsp2\\t(350,500,\\1a&HFF&)}д{\\r\\fscx110\\fscy120\\fsp2\\t(350,500,\\1a&HFF&)}а{\\r\\fscx110\\fscy120\\fsp2\\t(500,650,\\1a&HFF&)}к{\\r\\fscx110\\fscy120\\fsp2\\t(600,750,\\1a&HFF&)}ц{\\fscx110\\fscy120\\fsp2\\t(250,400,\\1a&HFF&)}и{\\r\\fscx110\\fscy120\\fsp2\\t(0,150,\\1a&HFF&)}я: {\\r\\fscx110\\fscy120\\fsp2\\t(550,700,\\1a&HFF&)}n{\\r\\fscx110\\fscy120\\fsp2\\t(50,200,\\1a&HFF&)}e{\\r\\fscx110\\fscy120\\fsp2\\t(650,800,\\1a&HFF&)}u{\\r\\fscx110\\fscy120\\fsp2\\t(200,350,\\1a&HFF&)}t{\\r\\fscx110\\fscy120\\fsp2\\t(300,600,\\1a&HFF&)}r{\\r\\fscx110\\fscy120\\fsp2\\t(700,850,\\1a&HFF&)}a{\\r\\fscx110\\fscy120\\fsp2\\t(250,400,\\1a&HFF&)}l'''
	tmp = re.sub(r'\{\\[^\}]*\}', '', sss)
	print '\n-------------'
	print unicode(tmp, 'utf-8').encode('ascii', 'xmlcharrefreplace')



