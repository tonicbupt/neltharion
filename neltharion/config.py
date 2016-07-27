# coding: utf-8

BASE_DIR = '/mnt/mfs/fe/ems'

try:
    from .local_config import *
except ImportError:
    pass
