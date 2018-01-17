# -*- coding: utf-8 -*-

import sys
import os

# Temporary hack to pack resources in one file without modification of my code
path = getattr(sys, '_MEIPASS', os.getcwd())
os.chdir(path)
