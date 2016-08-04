# coding: utf-8

import logging
from flask import Flask, jsonify, request, render_template

from neltharion.job import do_compile
from neltharion.models import App


logging.getLogger('requests').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(asctime)s: %(message)s')


app = Flask(__name__)
log = logging.getLogger(__name__)


@app.route('/')
def index():
    apps = App.get_all()
    return render_template('app_list.html', apps=apps)


@app.route('/app/<path:appname>')
def get_app(appname):
    app = App.get(appname)
    if not app:
        return render_template('404.html'), 404

    versions = app.get_versions()

    release = app.get_release()
    pre = app.get_pre()

    release_sha = release and release.sha or ''
    pre_sha = pre and pre.sha or ''
    return render_template('app.html', app=app, versions=versions, release_sha=release_sha, pre_sha=pre_sha)


@app.route('/hook', methods=['POST'])
def gitlab_hook():
    data = request.get_json()
    log.info('build status: %s', data['build_status'])
    if data['build_status'] != 'success':
        return 'ok'

    do_compile(str(data['repository']['git_ssh_url']), str(data['repository']['name']), str(data['sha']))
    return 'ok'


@app.route('/api/app')
def get_apps():
    apps = App.get_all()
    return jsonify([app.to_dict() for app in apps])


@app.route('/api/app/<path:appname>/versions')
def versions(appname):
    app = App.get(appname)
    if not app:
        return jsonify({'error': 'app not found'}), 404

    versions = app.get_versions()
    release = app.get_release()
    return jsonify({
        'release': release and release.to_dict() or None,
        'versions': [v.to_dict() for v in versions],
    })


@app.route('/api/app/<path:appname>/version/<sha>/deploy', methods=['POST'])
def deploy(appname, sha):
    app = App.get(appname)
    if not app:
        return jsonify({'error': 'app not found'}), 404

    version = app.get_version(sha)
    if not version:
        return jsonify({'error': 'version not found'}), 404

    stage = request.form.get('stage', '')
    if stage == 'release':
        version.deploy_release()
    elif stage == 'pre':
        version.deploy_pre()
    return jsonify({'error': None})


@app.route('/api/app/<path:appname>/version/<sha>/delete', methods=['POST'])
def delete(appname, sha):
    app = App.get(appname)
    if not app:
        return jsonify({'error': 'app not found'}), 404

    version = app.get_version(sha)
    if not version:
        return jsonify({'error': 'version not found'}), 404

    version.delete()
    return jsonify({'error': None})
