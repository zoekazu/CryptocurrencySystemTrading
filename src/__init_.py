#!/usr/bin/env python3
import glob
import os

from . import bitflyer

__all__ = [
    os.path.split(os.path.splitext(file)[0])[1]
    for file in glob.glob(os.path.join(os.path.dirname(__file__), '[a-zA-Z]*.py'))
]

if (__name__ == '__main__'):
    print(__all__)
