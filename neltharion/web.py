# coding: utf-8

from flask import Flask, jsonify, request

from neltharion.job import do_compile
from neltharion.models import App


app = Flask(__name__)


@app.route('/hook', methods=['POST'])
def gitlab_hook():
    data = request.get_json()
    if not data['build_status'] == 'success':
        print data['build_status']
        return 'ok'

    do_compile(str(data['repository']['git_ssh_url']), str(data['repository']['name']), str(data['sha']))
    return 'ok'


@app.route('/app')
def get_apps():
    apps = App.get_all()
    return jsonify([app.to_dict() for app in apps])


@app.route('/app/<path:appname>/versions')
def versions(appname):
    app = App.get(appname)
    if not app:
        return jsonify({'error': 'app not found'}), 404

    versions = app.get_versions()
    current = app.get_current()
    return jsonify({
        'current': current and current.to_dict() or None,
        'versions': [v.to_dict() for v in versions],
    })


@app.route('/app/<path:appname>/version/<sha>/deploy', methods=['POST'])
def deploy(appname, sha):
    app = App.get(appname)
    if not app:
        return jsonify({'error': 'app not found'}), 404

    version = app.get_version(sha)
    if not version:
        return jsonify({'error': 'version not found'}), 404

    version.deploy()
    return jsonify({'error': None})
