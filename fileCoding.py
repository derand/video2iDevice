#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
#import chardet
import codecs

def file_encoding(filename):
        data = open(filename).read()
        #with open(filename) as codefile:
        #data = codefile.read()
        try:
            import chardet
            return chardet.detect(data)['encoding']
        except ImportError:
            sys.path.append('chardet')
            import universaldetector
            u = universaldetector.UniversalDetector()
            u.reset()
            u.feed(data)
            u.close()
            return u.result['encoding']
    
if __name__=='__main__':
    if len(sys.argv)==2:
        print file_encoding(sys.argv[1])
