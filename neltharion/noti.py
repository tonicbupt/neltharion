# coding: utf-8

import logging
import requests

from neltharion.config import SLACK_USERS, NOTBOT_URL


log = logging.getLogger(__name__)


def send_slack_noti(content):
    payload = {
        'to': SLACK_USERS,
        'subject': '',
        'content': content,
    }
    try:
        requests.post(NOTBOT_URL, payload)
    except Exception as e:
        log.exception(e)
