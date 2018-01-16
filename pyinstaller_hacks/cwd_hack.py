import sys
import os

path = getattr(sys, '_MEIPASS', os.getcwd())
os.chdir(path)
