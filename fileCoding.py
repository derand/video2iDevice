#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import chardet
import codecs

def code_detecter(filename):
	with open(filename) as codefile:
		data = codefile.read()
		#print data
    	print chardet.detect(data)
    
	return chardet.detect(data)['encoding']
    
if __name__=='__main__':
	if len(sys.argv)==2:
		code_detecter(sys.argv[1])
