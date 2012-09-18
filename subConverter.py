#!/usr/bin/env python
# -*- coding: utf-8 -*-

# writed by derand
# - Sorry for horrible code -

import re
import glob
import sys
import os
import string
import fileCoding

STTNGS = {
	# remove this items from result
'ASSremoveItems' : ('Song123', 'song345' ),

	# change color
'subStyleColors' : {
	# by style name
	"prew" : "d9a1afi",
	"end" : "d37f63i",
	"rus_op" : "8ad3a1i",
	"rus_ed" : "8ad3a1i",
	"eng_op" : "9292e6i",
	"eng_ed" : "9292e6i",
	
	"Note" : "b3ddb5<",

	# by author
	",Keiichi" : "ffcf9e",
	",Rena" : "ffbea4",
	",Mion" : "b7ffad",
	",Satoko" : "fbffb8",
	",Rika" : "c3ccff",
	",Shion" : "b1ffdd",
	",Hanyuu" : "cff4ff",
	",Oishi" : "eaddd9",
	"Opening" : "123456i"
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
	unicode("Вон туда.", 'utf-8'): {
			"text": unicode("Вон туда.", 'utf-8'),
			"outStyle": "808080[",
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

	def __compareLines(self, val1, val2):
		# val = [[_style, _name], self.timesrt(elems[1]), subEnd, linetext8, []]
		return val1[0][0]==val2[0][0] and val1[0][1]==val2[0][1] and val1[1]==val2[1] and val1[2]==val2[2] and val1[3]==val2[3]

	def __insert(self, arr, val):
		if len(arr)==0:
			arr.append(val)
		elif len(arr)==1:
			if not self.__compareLines(arr[0], val):
				if self.time2int(val[1])>self.time2int(arr[0][1]):
					arr.append(val)
				else:
					arr.insert(0, val)
		else:
			s = ''
			x = self.time2int(val[1])
			if x>=self.time2int(arr[-1][1]):
				if not self.__compareLines(arr[-1], val):
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

				if not self.__compareLines(arr[i], val):
					arr.insert(i, val)
	
	def postProcessing(self, s):
		"""
			combine one chars lines
		"""
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
				txt = '&lt;%s&gt;'%(txt)
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
						fo.write('%d\n%s --> %s\n%s\n\n'%(num, lastTm.encode('utf-8'), tm.encode('utf-8'), self.postProcessing("\n".join(s))) )
						num += 1
				#lastTm = self.int2time(self.time2int(tm)+20)
				lastTm = tm

		fo.close()


	def writeOut2ttxt(self, fname_ttxt, lines):
		'''
				write lines to ttxt format
		'''
		
		#print lines[90]
		#print lines[90][3]
		#sys.exit(0)
		
		s = ''
		subs = self.groupByTime(lines)

		num = 1
		fo = open(fname_ttxt,'w')
		fo.write('''<?xml version="1.0" encoding="UTF-8" ?>

<TextStream version="1.1">
<TextStreamHeader width="400" height="60" layer="0" translation_x="0" translation_y="0">
<TextSampleDescription horizontalJustification="center" verticalJustification="bottom" backColor="0 0 0 0" verticalText="no" fillTextRegion="no" continuousKaraoke="no" scroll="None">

<FontTable>
<FontTableEntry fontName="Serif" fontID="1"/>
</FontTable>

<TextBox top="0" left="0" bottom="60" right="400"/>
<Style styles="Normal" fontID="1" fontSize="18" color="ff ff ff ff"/>

</TextSampleDescription>
</TextStreamHeader>''')
		lastSubTm = '00:00:00.000'
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
			#print ""
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
				#print maxLines,linesByTime

				s = []
				_now = []
				for j in range(maxLines):
					s.append(None)
					_now.append(None)
				tmp = []
				for l in linesByTime: tmp.append(l)
				for k in range(len(_prew)):
					#break
					for n in range(len(tmp)):
						if tmp[n]==_prew[k]:
							s[k] = tmp[n]
							_now[k] = tmp[n]
							tmp.remove(tmp[n])
							break
				for l in tmp:
					j=0
					while s[j]!=None:
						j+=1
					s[j] = l
					_now[j] = l
				_prew = _now
				while s[0]==None:
					s = s[1:]

				#print s
				if s!=[]:
					if self.time2int(lastTm)<self.time2int(tm):
						tmFrom = (lastTm[:-4]+'.'+lastTm[-3:]).encode('utf-8')
						tmTo = (tm[:-4]+'.'+tm[-3:]).encode('utf-8')
						#print tmFrom, tmTo
						#sub = '¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶В¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶¶а¶'
						#__tags = [[0, 50, 'color="38 38 38 40"'],]
						sub = ''
						__tags = []
						for l in s:
							subStyles = ''
							subLen = len(unicode(sub, 'utf-8'))
							if l==None:
								color = '38 38 38 00'
								subStyles =' color="%s"'%color
								if len(sub):
									sub = '%s\n¶'%sub
									__tags.append([subLen+1, subLen+2, subStyles])
								else:
									sub = '¶'
									__tags.append([subLen, subLen+1, subStyles])
							else:
								add = l[3].replace('&lt;', '<').replace('&gt;', '>')
								#print '--', l[0], l[1], l[2], l[3], l[4]
								_len = len(unicode(add, 'utf-8'))
								if len(l[4]):
									for style in l[4]:
										_start = 0
										_end = _len
										color = 'ffffff'
										subStyles = ''
										__inc = 0
										for j in range(len(style[0])):
											if style[0][j]=='#':
												color = style[0][j+1:j+7]
												j+=6
											elif style[0][j]=='i':
												subStyles = subStyles+',Italic'
											elif style[0][j]=='u':
												pass
											elif style[0][j]=='<':
												add = '<%s>'%add
												__inc+=1
											elif style[0][j]=='[':
												add = '[%s]'%add
												__inc+=1
										
										# set style lenght
										if len(style)>2:
											_start = style[1]
											_end = style[2]

										# fix styles length if changed line length
										if __inc>0:
											for j in range(len(__tags)):
												val = __tags[j]
												if len(sub) and (subLen+1)==val[0]:
													val[1] += 1
												if len(sub)==0 and subLen==val[0]:
													val[1] += 1
												if len(sub) and (subLen+1+_len)==val[1]:
													val[1] += 1
												if len(sub)==0 and (subLen+_len)==val[0]:
													val[1] += 1
												__tags[j] = val
											_end += __inc*2
	
										if len(subStyles)>0: subStyles = ' styles="%s"'%subStyles[1:]
										color = '%s %s %s ff'%(color[0:2], color[2:4], color[4:6])
										color = color.lower()
										if color<>'ff ff ff ff':
											subStyles = subStyles+' color="%s"'%color
										#subLen = len(unicode(sub, 'utf-8'))
										if len(sub):
											#sub = '%s\n%s'%(sub, add)
											if len(subStyles)>0:
												if len(__tags):
													__lastStyle = __tags[-1]
													if __lastStyle[2]==subStyles and __lastStyle[1]==(subLen+_start):
														__lastStyle[1] = subLen+1+_end
													else:
														__tags.append([subLen+_start, subLen+1+_end, subStyles])
												else:
													__tags.append([subLen+_start, subLen+1+_end, subStyles])
												#tags = '%s<Style fromChar="%d" toChar="%d" %s/>'%(tags, subLen+1+_start, subLen+1+_end, subStyles)
										else:
											#sub = '%s'%add
											if len(subStyles)>0:
												__tags.append([subLen+_start, subLen+_end, subStyles])
												#tags = '%s<Style fromChar="%d" toChar="%d" %s/>'%(tags, subLen+_start, subLen+_end, subStyles)
								if len(sub):
									sub = '%s\n%s'%(sub, add)
								else:
									sub = '%s'%add

						tags = ''
						#for __t in sorted(__tags, key=lambda el: el[1]-el[0]):
						for __t in __tags:
							tags = '%s<Style fromChar="%d" toChar="%d" %s/>'%(tags, __t[0], __t[1], __t[2])
								
						#sub = sub.replace('<', '&lt;').replace('>', '&gt;').replace('¶', '&nbsp;')
						#sub = sub.replace('<', '&lt;').replace('>', '&gt;').replace('¶', ' ')
						sub = sub.replace('<', '&lt;').replace('>', '&gt;').replace('¶', '.')
						if lastSubTm<>tmFrom:
							fo.write('\n<TextSample sampleTime="%s" xml:space="preserve"></TextSample>'%lastSubTm)
						#print'%s%s'%(sub,tags.encode('utf-8'))
						fo.write('\n<TextSample sampleTime="%s" xml:space="preserve">%s%s</TextSample>'%(tmFrom, sub, tags.encode('utf-8')))
						lastSubTm = tmTo
						#fo.write('%d\n%s --> %s\n%s\n\n'%(num, lastTm.encode('utf-8'), tm.encode('utf-8'), self.postProcessing("\n".join(s))) )
						#str = self.postProcessing("\n".join(s))
						#print len(unicode(str, 'utf-8')), str
						num += 1
				#lastTm = self.int2time(self.time2int(tm)+20)
				lastTm = tm

		fo.write('\n<TextSample sampleTime="%s" xml:space="preserve"></TextSample>'%lastSubTm)
		fo.write('\n</TextStream>\n');
		fo.close()


	def getSubStyle(self, st, defStyles):
		rv = None
		if self.__STNGS.has_key('subStyleColors'):
			for key in self.__STNGS['subStyleColors']:
				tmp = key.encode( "utf-8" ).split(',')
				if len(tmp)==1:
					if key.encode( "utf-8" )==st[0]:
						rv = self.__STNGS['subStyleColors'][key].encode( "utf-8" )
						break
				else:
					if tmp[1]==st[1] and (tmp[0]=='' or tmp[0]==st[0]):
						rv = self.__STNGS['subStyleColors'][key].encode( "utf-8" )
						break
		if rv==None and defStyles.has_key(st[0]):
			rv = defStyles[st[0]]
		return rv

	def firstTagBounds(self, line, tags, add=0):
		tag = None
		min_pos = -1
		for __tag in tags:
			srch = '<%s>'%__tag
			if __tag[-1]==' ':
				srch = srch[:-1]
			idx = line.find(srch);
			if (min_pos==-1 or min_pos>idx) and idx<>-1:
				min_pos = idx
				tag = __tag
		if tag==None:
			return (None, -1, -1)
		if tag[-1]==' ':
			srch = srch[:-1]
			tag = tag[:-1]
		# search right close tag index
		end_pos = line.find('</%s>'%tag)
		__add=0
		while end_pos>-1:
			__idx = line[__add:].find(srch)+__add
			if __idx<=__add or __idx>end_pos:
				break
			__add = end_pos+1
			end_pos = line[__add:].find('</%s>'%tag)+__add
		if tag<>None and end_pos==-1 and len(tag)>1:
			return (tag, min_pos, len(line))
		if tag<>None and end_pos<=min_pos:
			return self.firstTagBounds(line[min_pos+1:], tags, add+min_pos)
		return (tag, min_pos, end_pos)

	def tagsBounds(self, line, tags, bounds=[], add=0):
		(tag, min_pos, end_pos) = self.firstTagBounds(line, tags)
		while tag<>None:
			idx = min_pos+line[min_pos:].find('>')+1
			b = []
			if tag=='font':
				srch = re.compile('\s+color\s*=\s*[\'\"]{0,1}(\#[a-fA-F0-9]{6})[\'\"]{0,1}').search(line[min_pos:idx])
				if srch==None:
					srch = re.compile('\s+size').search(line[min_pos:idx])
					if srch==None:
						print 'Error on line: "%s"'%line
						sys.exit(1)
					b.append('#ffffff')
				else:
					b.append(srch.groups()[0])
			else:
				b.append(tag)
			
			if len(b)>0:
				b.append(add+min_pos)
				(converted_line,bounds) = self.tagsBounds(line[idx:end_pos], tags, bounds, b[-1])
				#end_pos = line.find('</%s>'%tag)
				tmp_line = line[:min_pos]+converted_line
				line = tmp_line+line[end_pos+len('</%s>'%tag):]
				b.append(add+len(tmp_line))
				bounds.insert(0, b)
			(tag, min_pos, end_pos) = self.firstTagBounds(line, tags)
		return line,bounds

	def stylesFromSrtLine(self, line):
		(l, styles) = self.tagsBounds(line, ['font ', 'i'], [])

		#merge equal bounds tags, remove bounds from full-line sub
		styles = sorted(styles, key=lambda el: el[1])
		__tmp = []
		for i in range(len(styles)):
			if len(__tmp) and __tmp[-1][1]==styles[i][1] and __tmp[-1][2]==styles[i][2]:
				__tmp[-1][0] += styles[i][0]
			else:
				__tmp.append(styles[i])
		styles = []
		for s in __tmp:
			if s[1]==0 and s[2]==len(l):
				styles.append([s[0],])
			else:
				styles.append(s)
		return (l, styles)

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
		canMergeLines = True
		fCoding = fileCoding.file_encoding(fname_ass)
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
			if line[:8] == 'alogue: ':
				line = 'Di%s'%line
			if line[:10] == 'Dialogue: ':
				block = 3
			if block==3:
				#print line
				if line[:8] == 'alogue: ':
					line = 'Di%s'%line
				if line[:10] == 'Dialogue: ':
					line = line[8:]
					elems = line.split(',')
					linetext = ",".join(elems[9:])
					linetext = unicode(linetext, fCoding)

					#if len(linetext)>12 and ((linetext[:7]=='{\\bord3') or (linetext[:5]=='{\\be1')) and (len(elems[3])>3 and elems[3][:3]=="ed_"):
					#	linetext=''
					#if len(linetext)>12 and (linetext[:15]=='{\\fad(200,200)}') and (len(elems[3])>3 and elems[3][:3]=="ed_"):
					#	linetext=''

					linetext = linetext.replace('\\n','\\N')
					linetext = linetext.replace('\\N','\n')
					linetext = re.sub(r'\{\\[^\}]*\}', '', linetext)
					linetext = re.sub(r'([lmb](\s\-{0,1}\d+){2,8}\s{0,1}){2,}', '', linetext)	# m 0 0 l 0 150 l 250 150 l 250 0
					linetext = re.sub(r'm\s\-{0,1}\d+\s+\-{0,1}\d+\s+s(\s+\-{0,1}\d+){14}\s+c', '', linetext)	# m 5 0 s 95 0 100 5 100 95 95 100 5 100 0 95 0 5 c
					linetext = linetext.replace('\\h','')
					linetext = re.sub(r'\{[^\}]*\}', '', linetext)		# remove from subs comments {xxxx}

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
							if style==unicode(elems[3], 'utf-8'):
								bl = True
								break
						if bl:
							continue

					while linetext.find('\n\n')>=0:
						linetext = linetext.replace('\n\n','\n')
					tmpStr = ''
					canMerge = True
					for l in linetext.split('\n'):
						ch = '\n'
						if l.find(' ')==-1 and l.find('.')==-1 and l.find(',')==-1:
							if canMerge:
								ch = ' '
							canMerge = True
						else:
							canMerge = False
						tmpStr = '%s%s%s'%(tmpStr, ch, l)
					linetext = tmpStr.strip()
					linetext8 = linetext.encode('utf-8')
					#print len(unicode(linetext,'utf-8')),linetext
					if len(linetext8)>0:
						_style = elems[3].strip()
						if _style[0]=='*': _style = _style[1:]
						_name = elems[4].strip()
						val = [[_style, _name], self.timesrt(elems[1]), subEnd, linetext8, []]
						if lastVal<>None:
							if canMergeLines and lastVal[0][0]==val[0][0] and lastVal[1]==val[1] and lastVal[2]==lastVal[2] and linetext.find(' ')==-1 and linetext.find('.')==-1 and linetext.find(',')==-1:
								lastVal[3] = '%s %s'%(unicode(lastVal[3], 'utf-8'), linetext)
								lastVal[3] = lastVal[3].encode('utf-8')
							else:
								self.__insert(lines, val)
								lastVal = val
						else:
							self.__insert(lines, val)
							lastVal = val
						canMergeLines = (linetext.find(' ')==-1 and linetext.find('.')==-1 and linetext.find(',')==-1)

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
			style = self.getSubStyle(l[0], styles)
			if c != None and c != style:
				needFontTag = True
				break
			c = style

		if needFontTag:
			for i in range(len(lines)):
				l = lines[i]
				style = self.getSubStyle(l[0], styles)
				strLineStyle = self.stylesFromSrtLine(unicode(l[3], 'utf-8'))
				if style!=None:
					if strLineStyle[1]==[]:
						lines[i][4].append(("#%s"%style,))
				if strLineStyle[1]!=[]:
					lines[i][3] = strLineStyle[0].encode('utf-8')
					for s in strLineStyle[1]:
						lines[i][4].append(s)
		return lines

	def readSrt(self, fname_srt):
		fi = open(fname_srt)
		idx = None
		tm = None
		txt = None
		lastLineEmpty = True
		set = False
		lines = []
		subReplace = {}
		if self.__STNGS.has_key('subReplace'):
			subReplace = self.__STNGS['subReplace']
		subStyle = None
		fCoding = fileCoding.file_encoding(fname_srt)
		for line in fi:
			line = unicode(line, fCoding).strip()
			if len(line)>3 and line[:3]==u'\xEF\xBB\xBF':
				line = line[3:]

			line = re.sub(r'\{\\[^\}]*\}', '', line)
			
			if len(line)!=0:
				
				subStyle = []
				if subReplace.has_key(line):
					if subReplace[line].has_key('text'):
						line = subReplace[line]['text']

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
							val = (['', ''], tm1, tm2, txt.encode('utf-8'), subStyle)
							self.__insert(lines, val)
							if len(subStyle)>0:
								sys.exit(0)
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
						txt += u'\n%s'%line
				set= False
				lastLineEmpty = False
			else:
				lastLineEmpty = True

		if idx!=None and tm!=None and txt!=None:
			ttt = tm.split('-->')
			if len(ttt)==2:
				tm1 = ttt[0].strip()
				tm2 = ttt[1].strip()
				val = (['', ''], ttt[0].strip(), ttt[1].strip(), txt.encode('utf-8'), subStyle)
				self.__insert(lines, val)
		fi.close()

		# join lines in sub if lines > 2
		for i in range(len(lines)):
			val = lines[i]
			if len(val[3].split('\n'))>2:
				tmp = string.join(val[3].split('\n'), ' ')
				val = (val[0], val[1], val[2], tmp, val[4])
				lines[i] = val
		
		for i in range(len(lines)):
			val = lines[i]
			tmp = self.stylesFromSrtLine(unicode(val[3], 'utf-8'))
			if len(tmp[1]):
				val = (val[0], val[1], val[2], tmp[0].encode('utf-8'), tmp[1])
				lines[i] = val
			#print '%s %s'%(val[4], val[3])

		return lines

	def timeAdd(self, lines, time):
		tmp = []
		for i in range(len(lines)):
			val = lines[i]
			tm1 = self.int2time(self.time2int(val[1])+time)
			tm2 = self.int2time(self.time2int(val[2])+time)
			val = (val[0], tm1, tm2, val[3], val[4])
			#lines[i] = val
			if self.time2int(val[1])>0:
				tmp.append(val)
		lines = tmp
		return lines

	def ass2srt(self, fname_ass, fname_srt, sttngs={}):
		lines = self.readAss(fname_ass)

		if sttngs.has_key('addTimeDiff'):
			lines = self.timeAdd(lines, sttngs['addTimeDiff'])

		self.writeOut2srt(fname_srt, lines)
		return fname_srt

	def ass2ttxt(self, fname_ass, fname_ttxt, sttngs={}):
		lines = self.readAss(fname_ass)
		'''
		for i in range(len(lines)):
			val = lines[i]
			tm1 = self.int2time(self.time2int(val[1])+550)
			tm2 = self.int2time(self.time2int(val[2])+550)
			val = (val[0], tm1, tm2, val[3], val[4])
			lines[i] = val
		'''
		print '----------',sttngs
		
		if sttngs.has_key('addTimeDiff'):
			lines = self.timeAdd(lines, sttngs['addTimeDiff'])

		self.writeOut2ttxt(fname_ttxt, lines)
		return fname_ttxt

	def srt2ttxt(self, fname_srt, fname_ttxt, sttngs={}):
		lines = self.readSrt(fname_srt)

		if sttngs.has_key('addTimeDiff'):
			lines = self.timeAdd(lines, sttngs['addTimeDiff'])

		self.writeOut2ttxt(fname_ttxt, lines)
		return fname_ttxt

	def srt2srt(self, fname_srt1, fname_srt2=None, sttngs={}):
		tmp_fn = fname_srt2
		if fname_srt1==fname_srt2 or fname_srt2==None:
			tmp_fn = "%s.tmp"%fname_srt1

		lines = self.readSrt(fname_srt1)

		if sttngs.has_key('addTimeDiff'):
			lines = self.timeAdd(lines, sttngs['addTimeDiff'])

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
	#sc = subConverter(STTNGS)
	#print sc.stylesFromSrtLine(unicode('''<font color=#6BCBE6> Ты же был моим охранником.\nРазве ты не предан своей работе?!''', 'utf-8'))
	#sys.exit(0)
	if len(sys.argv)==2:
		sc = subConverter(STTNGS)
		#sc.stylesFromSrtLine(unicode('<i><font color="#b9d4b5">Потому что ты и только ты</font></i>', 'utf-8'))
		#sc.stylesFromSrtLine(unicode('<i><font color="#b9d4b5">Потому</font> что</i> ты<i> и</i> только ты', 'utf-8'))
		if sys.argv[1][-4:]=='.srt':
			fname_ttxt = os.path.basename(re.compile('\\.srt$').sub('.ttxt', sys.argv[1]))
			sc.srt2ttxt(sys.argv[1], fname_ttxt)
		else:
			#fname_ttxt = os.path.basename(re.compile('\\.ass$').sub('.ttxt', sys.argv[1]))
			#print sys.argv[1], fname_ttxt
			#sc.ass2ttxt(sys.argv[1], fname_ttxt)
			fname_ttxt = os.path.basename(re.compile('\\.ass$').sub('.ttxt', sys.argv[1]))
			print sys.argv[1], fname_ttxt
			sc.ass2ttxt(sys.argv[1], fname_ttxt)
	elif len(sys.argv)>2:
		if sys.argv[1]=='-styles':
			sc = subConverter(STTNGS)
			st = {}
			for i in range(2, len(sys.argv)):
				st = sc.readAssStyles(sys.argv[i], st)
			keys = st.keys()
			keys.sort()
			for key in keys:
				print "\t\"%s\" : \"%s\","%(key, st[key][0]) 
			
	

	sss = '''{\\r\\fscx110\\fscy120\\fsp2\\t(400,550,\\1a&HFF&)}р{\\r\\fscx110\\fscy120\\fsp2\\t(100,250,\\1a&HFF&)}е{\\rfscx110\\fscy120\\fsp2\\t(350,500,\\1a&HFF&)}д{\\r\\fscx110\\fscy120\\fsp2\\t(350,500,\\1a&HFF&)}а{\\r\\fscx110\\fscy120\\fsp2\\t(500,650,\\1a&HFF&)}к{\\r\\fscx110\\fscy120\\fsp2\\t(600,750,\\1a&HFF&)}ц{\\fscx110\\fscy120\\fsp2\\t(250,400,\\1a&HFF&)}и{\\r\\fscx110\\fscy120\\fsp2\\t(0,150,\\1a&HFF&)}я: {\\r\\fscx110\\fscy120\\fsp2\\t(550,700,\\1a&HFF&)}n{\\r\\fscx110\\fscy120\\fsp2\\t(50,200,\\1a&HFF&)}e{\\r\\fscx110\\fscy120\\fsp2\\t(650,800,\\1a&HFF&)}u{\\r\\fscx110\\fscy120\\fsp2\\t(200,350,\\1a&HFF&)}t{\\r\\fscx110\\fscy120\\fsp2\\t(300,600,\\1a&HFF&)}r{\\r\\fscx110\\fscy120\\fsp2\\t(700,850,\\1a&HFF&)}a{\\r\\fscx110\\fscy120\\fsp2\\t(250,400,\\1a&HFF&)}l'''
	tmp = re.sub(r'\{\\[^\}]*\}', '', sss)
	print '\n-------------'
	print unicode(tmp, 'utf-8').encode('ascii', 'xmlcharrefreplace')
	
	linetext = '{\p1\fscx76.25\fscy97.5\frz328.141\pos(578,189)}m -105 68 l -91 39 l -77 68 l -80 68 l -84 59 l -98 59 l -102 68 m -73 68 l -73 39 l -64 39 b -54 39 -48 44 -48 54 b -48 65 -55 68 -64 68 m -32 68 l -45 39 l -41 39 l -32 61 l -22 39 l -19 39 m -18 68 b -21 68 -21 66 -21 62 b -22 60 -22 59 -20 56 b -17 51 -15 41 -10 36 b -9 34 -9 29 -7 26 l -9 25 l -4 16 b -5 16 -7 15 -6 14 b -5 13 -8 13 -9 13 b -12 11 -13 10 -13 6 b -11 4 -11 -2 -10 -6 b -10 -8 -7 -8 -5 -9 b -3 -10 -3 -11 -3 -12 b -3 -14 -5 -14 -7 -12 b -7 -14 -10 -12 -12 -13 b -10 -15 -9 -15 -8 -16 l -11 -16 b -9 -17 -7 -18 -7 -21 b -7 -24 -7 -26 -5 -28 b -4 -29 -1 -29 0 -27 l -1 -30 b 1 -28 3 -29 2 -26 b 4 -27 6 -26 7 -24 b 7 -27 10 -26 12 -28 b 10 -24 13 -24 14 -21 b 15 -18 14 -15 12 -13 b 19 -10 9 -8 14 -6 b 13 -6 11 -6 10 -7 b 12 -10 8 -10 7 -11 l 6 -14 b 5 -12 4 -11 2 -10 b 2 -9 5 -9 8 -8 b 15 -3 19 1 19 2 b 19 4 17 7 9 7 b 13 13 12 18 14 20 b 14 21 13 22 12 22 b 13 27 12 31 12 34 b 13 44 11 51 10 55 l 10 58 b 12 59 10 61 10 62 b 11 67 10 68 7 68 b 5 68 3 67 3 65 b 3 63 6 62 7 58 b 7 51 7 47 7 39 b 7 35 6 30 5 26 b 4 26 2 26 1 26 b -3 33 -4 37 -8 42 b -10 48 -11 50 -17 58 b -17 61 -16 63 -13 66 b -13 68 -16 68 -17 68 m 16 68 l 16 39 l 36 61 l 36 39 l 39 39 l 39 68 l 19 47 l 19 68 m 49 68 l 49 41 l 43 41 l 43 39 l 58 39 l 58 41 l 52 41 l 52 68 m 61 68 l 74 39 l 88 68 l 85 68 l 81 59 l 68 59 l 64 68 m 110 54 l 122 54 b 123 65 113 69 107 69 b 102 69 92 65 92 54 b 92 45 99 39 107 39 b 114 39 117 41 121 44 l 119 47 b 115 44 113 42 107 42 b 101 42 95 46 95 54 b 95 63 103 66 107 66 b 113 66 118 64 119 57 l 110 57 m 128 68 l 128 39 l 145 39 l 145 42 l 131 42 l 131 51 l 145 51 l 145 54 l 131 54 l 131 65 l 145 65 l 145 68 m -86 56 l -91 46 l -96 56 m -70 42 l -70 66 l -65 66 b -59 66 -50 63 -51 54 b -51 46 -57 42 -65 42 m 79 56 l 74 45 l 69 56 m -4 11 b -4 8 -5 6 -6 4 b -7 4 -9 8 -7 9 m 6 3 b 6 4 6 5 7 5 b 8 4 11 3 12 2 b 10 1 8 0 6 -2 {\p0}'
	linetext = re.sub(r'\{\\[^\}]*\}', '', linetext)
	linetext = re.sub(r'([lmb](\s\-{0,1}\d+){2,6}\s{0,1}){2,}', '', linetext)	# m 0 0 l 0 150 l 250 150 l 250 0
	linetext = re.sub(r'm\s\-{0,1}\d+\s+\-{0,1}\d+\s+s(\s+\-{0,1}\d+){14}\s+c', '', linetext)
	print "-%s-"%linetext


