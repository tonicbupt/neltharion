# coding: utf-8

import os
import json
import shutil
import envoy
import gevent
import logging
import tempfile
import contextlib
from functools import wraps

from neltharion.models import Version
from neltharion.noti import send_slack_noti


log = logging.getLogger(__name__)


class JobError(Exception):
    pass


@contextlib.contextmanager
def _temp_work_dir(prefix='neltharion-'):
    workdir = tempfile.mkdtemp(prefix=prefix)
    try:
        yield workdir
    finally:
        if not os.path.lexists(workdir):
            return
        if os.path.islink(workdir):
            os.unlink(workdir)
        else:
            shutil.rmtree(workdir)


@contextlib.contextmanager
def _temp_change_dir(path):
    current = os.getcwd()
    try:
        os.chdir(path)
        yield path
    finally:
        os.chdir(current)


def run_command(command):
    r = envoy.run(command)
    if r.status_code:
        raise JobError(r.std_err)
    return r


def use_gevent(f):
    @wraps(f)
    def _(*args, **kwargs):
        return gevent.spawn(f, *args, **kwargs)
    return _


@use_gevent
def do_compile(repo, project, git_hash):
    try:
        _do_compile(repo, project, git_hash)
    except JobError as e:
        send_slack_noti('Error when executing job (%s, %s, %s): %s' % (repo, project, git_hash, e.message))


def _do_compile(repo, project, git_hash):
    with _temp_work_dir() as workdir:
        os.chdir(workdir)
        # 1. clone code
        log.info('cloning %s to %s ...' % (repo, project))
        send_slack_noti('cloning %s to %s ...' % (repo, project))
        run_command('git clone %s %s' % (repo, project))
        send_slack_noti('cloning %s to %s done' % (repo, project))
        log.info('cloning %s to %s done' % (repo, project))
        # 2. run deploy.sh
        rules = {}
        with _temp_change_dir(project):
            if not os.path.lexists('rules'):
                raise JobError('No rules found in repository, ignore')
            if not os.path.lexists('compile.sh'):
                raise JobError('No compile.sh found in repository, ignore')

            log.info('read rules and compile.sh in %s ...' % project)
            send_slack_noti('read rules and compile.sh in %s ...' % project)
            # load rules
            with open('rules', 'r') as f:
                try:
                    rules = json.load(f)
                except ValueError:
                    return
            # run compile.sh
            log.info('execute compile.sh in %s ...' % project)
            send_slack_noti('execute compile.sh in %s ...' % project)
            run_command('sh compile.sh')

            # 3. copy files
            log.info('copy files for %s ...' % project)
            for src, dst in rules.iteritems():
                src_dir = os.path.join(workdir, project, src)
                if not os.path.lexists(src_dir):
                    continue
                    
                v = Version.create(dst, git_hash)
                v.transport(src_dir)
                log.info('%s --> %s' % (src_dir, dst))
                send_slack_noti('%s --> %s' % (src_dir, dst))
