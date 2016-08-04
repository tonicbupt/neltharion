# coding: utf-8

from optparse import OptionParser
from datetime import datetime, timedelta

from neltharion.models import App
from neltharion.noti import send_slack_noti


def get_threshold():
    parser = OptionParser()
    parser.add_option('-i', '--interval', dest='interval', help='days to keep, versions before this will be removed', default=7, type=int)
    options, _ = parser.parse_args()
    return datetime.now() - timedelta(days=options.interval)


def clean_app(app, threshold):
    for version in app.get_versions():
        if version.mtime > threshold:
            continue
        version.delete()


def clean(threshold):
    for app in App.get_all():
        clean_app(app, threshold)


def main():
    threshold = get_threshold()
    clean(threshold)
    send_slack_noti('%s 前的版本都删掉咯' % threshold)


if __name__ == '__main__':
    main()
