# author vish
# webpage eppur-si.appspot.com
# email avishalom@gmail.com
#
# patent pending on moveable partially hidden captcha application.
# use freely, but please attribute authorship where applicable.
# provided as is.

import io
import json
import hmac as hmaclib
import hashlib
import base64
import os
import sys

from flask import Flask, request, Response

sys.path.insert(0, os.path.dirname(__file__))
from modules import imagesH

app = Flask(__name__)

# Set CAPTCHA_SECRET in app.yaml env_variables or your shell for production.
SECRET = os.environ.get('CAPTCHA_SECRET', 'eppur-si-mouve-default').encode()


def _make_token(params):
    payload = base64.urlsafe_b64encode(
        json.dumps(params, sort_keys=True).encode()
    ).decode().rstrip('=')
    sig = hmaclib.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()[:16]
    return sig + payload


def _verify_token(token):
    if len(token) < 17:
        return None
    sig, raw = token[:16], token[16:]
    expected = hmaclib.new(SECRET, raw.encode(), hashlib.sha256).hexdigest()[:16]
    if not hmaclib.compare_digest(sig, expected):
        return None
    pad = -len(raw) % 4
    try:
        return json.loads(base64.urlsafe_b64decode(raw + '=' * pad))
    except Exception:
        return None


def _gif_response(params):
    word = params.get('word', 'default')
    conf = int(params.get('c', 1))
    v = imagesH.VISCHA(word, conf, params)
    buf = io.BytesIO()
    v.writeImage_fp(buf)
    buf.seek(0)
    return Response(buf.read(), mimetype='image/gif')


def _error_gif(message):
    return _gif_response({'word': message, 'screen_d': 15, 'c': '0', 'wordCount': '0'})


@app.route('/get_code')
def get_code():
    params = dict(request.args)
    token = _make_token(params)
    url = f"{request.host_url}gif/{token}.gif"
    return Response(url, mimetype='text/plain')


@app.route('/gif/<path:name>')
def serve_gif(name):
    if not name.endswith('.gif'):
        return _error_gif('not a gif')
    params = _verify_token(name[:-4])
    if params is None:
        return _error_gif('bad code')
    return _gif_response(params)


@app.route('/direct_gif')
def direct_gif():
    return _gif_response(dict(request.args))


@app.route('/decode/<path:name>')
def decode(name):
    if not name.endswith('.gif'):
        return Response('not a gif', status=400, mimetype='text/plain')
    params = _verify_token(name[:-4])
    if params is None:
        return Response('bad code', status=400, mimetype='text/plain')
    qs = '&'.join(f"{k}={v}" for k, v in params.items())
    return Response(f"{request.host_url}direct_gif?{qs}", mimetype='text/plain')


@app.route('/robots.txt')
def robots():
    path = os.path.join(os.path.dirname(__file__), 'robots.txt')
    with open(path) as f:
        return Response(f.read(), mimetype='text/plain')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    html_path = os.path.join(os.path.dirname(__file__), 'eppur.html')
    with open(html_path) as f:
        content = f.read().replace('<!--$HOST_REPL-->', request.host_url.rstrip('/'))
    return Response(content, mimetype='text/html')


if __name__ == '__main__':
    app.run(debug=True)
