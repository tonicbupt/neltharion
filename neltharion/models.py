# coding: utf-8

import os
import operator
import shutil
from os.path import exists, join, isdir
from datetime import datetime

from neltharion.config import BASE_DIR


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
            if f == 'current':
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

    def get_current(self):
        current = join(self.path, 'current')
        try:
            current_version = os.readlink(current)
        except OSError:
            return None

        p = join(self.path, current_version)
        stats = os.stat(p)
        return Version(self.name, current_version, datetime.fromtimestamp(stats.st_mtime))

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

    def deploy(self):
        app = App.get(self.name)
        dst = join(app.path, 'current')

        if exists(dst):
            os.unlink(dst)
        os.symlink(self.sha, dst)

    def to_dict(self):
        return {'name': self.name, 'sha': self.sha, 'mtime': self.mtime.strftime('%Y-%m-%d %H:%M:%S')}
