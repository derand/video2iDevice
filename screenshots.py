#!/usr/bin/env python
# -*- coding: utf-8 -*-

# writed by derand (2derand@gmail.com)

import os
import sys

if __name__=='__main__':
	fn = sys.argv[1]
	i = 0
	for idx in range(50, 7001, 50):
		cmd = 'ffmpeg -ss %d -vframes 1 -i %s -y -f image2 ./miku/sh_%04da.png'%(idx, fn, i)
		i+=1
		print cmd
		#os.system(cmd)
