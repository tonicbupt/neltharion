# coding: utf-8

BASE_DIR = '/mnt/mfs/fe/ems'
NOTBOT_URL = 'http://notbot.intra.ricebook.net/api/sendmsg.peter'
SLACK_USERS = '@lanbin;#deploy;@tonic;'

try:
    from .local_config import *
except ImportError:
    pass
