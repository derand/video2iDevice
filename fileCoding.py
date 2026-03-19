#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Utility module for detecting the character encoding of a file."""

import sys
import os
#import chardet
import codecs
from typing import Optional

def file_encoding(filename: str) -> Optional[str]:
    """Detect and return the character encoding of a file.

    Args:
        filename: Path to the file to inspect.

    Returns:
        Detected encoding name string (e.g. 'utf-8'), or None if detection fails.
    """
    with open(filename, 'rb') as f:
        data = f.read()
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
        print(file_encoding(sys.argv[1]))
