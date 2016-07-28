# coding: utf-8

import os
import operator
import shutil
from os.path import exists, join, isdir
from datetime import datetime

from neltharion.config import BASE_DIR


RELEASE_TAG = 'release'
PRE_TAG = 'pre'


class App(object):

    def __init__(self, name):
        self.name = name
        self.path = join(BASE_DIR, name)

    @classmethod
    def get_all(cls):
        appnames = join(BASE_DIR, '_all')
        if not exists(appnames):
            return []

        names = []
        with open(appnames, 'r') as f:
            for name in f:
                names.append(name.strip())
        return [cls(name) for name in names]

    @classmethod
    def get(cls, name):
        return cls(name) if exists(join(BASE_DIR, name)) else None

    def get_versions(self):
        if not exists(self.path):
            return []

        result = []
        for f in os.listdir(self.path):
            f = f.strip()
            if f in (RELEASE_TAG, PRE_TAG):
                continue

            path = join(self.path, f)
            if not isdir(path):
                continue

            stats = os.stat(path)
            result.append(Version(self.name, f, datetime.fromtimestamp(stats.st_mtime)))
        return sorted(result, key=operator.attrgetter('mtime'), reverse=True)

    def get_version(self, sha):
        versions = self.get_versions()
        for v in versions:
            if v.sha.startswith(sha):
                return v
        return None

    def _get_special(self, tag):
        version_file = join(self.path, '_' + tag)
        if not exists(version_file):
            return None

        with open(version_file, 'r') as f:
            version = f.read()

        p = join(self.path, version)
        stats = os.stat(p)
        return Version(self.name, version, datetime.fromtimestamp(stats.st_mtime))

    def get_release(self):
        return self._get_special(RELEASE_TAG)

    def get_pre(self):
        return self._get_special(PRE_TAG)

    def to_dict(self):
        return {'name': self.name, 'path': self.path}


class Version(object):

    def __init__(self, name, sha, mtime):
        self.name = name
        self.sha = sha
        self.mtime = mtime
        self.path = join(BASE_DIR, name, sha)

    @classmethod
    def create(cls, name, sha):
        v = cls(name, sha, datetime.now())
        if exists(v.path):
            shutil.rmtree(v.path)
        return v

    def transport(self, src):
        shutil.copytree(src, self.path)

    def _deploy_special(self, tag):
        app = App.get(self.name)
        dst = join(app.path, tag)
        special = join(app.path, '_' + tag)

        if exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(self.path, dst)
        with open(special, 'w') as f:
            f.write(self.sha)

    def deploy_release(self):
        self._deploy_special(RELEASE_TAG)

    def deploy_pre(self):
        self._deploy_special(PRE_TAG)

    def to_dict(self):
        return {'name': self.name, 'sha': self.sha, 'mtime': self.mtime.strftime('%Y-%m-%d %H:%M:%S')}
