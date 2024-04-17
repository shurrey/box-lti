import os
import json
import pprint
import urllib
import uuid
from tempfile import mkdtemp

from flask import Flask, render_template, jsonify
from flask import redirect, request
from flask_caching import Cache

from werkzeug.exceptions import Forbidden

import Config as config

from lti.login import Login
from lti.launch import Launch
from auth_redirect.auth_redirect import Auth_Redirect

PAGE_TITLE = 'Box LTI'

class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


app = Flask('Box LTI', template_folder='templates', static_folder='static')

app.wsgi_app = ReverseProxied(app.wsgi_app)

cache = Cache(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    return 200

@app.route('/login/', methods=['GET', 'POST'])
def login():

    login = Login()

    location, error = login.oidc_login(request)
    if error is not None:
        return location, error
    
    return redirect(location)

@app.route('/launch/', methods=['HEAD', 'GET', 'POST'])
def launch():
    launch = Launch()

    location, error = launch(request)

    if error is not None:
        return location, error
    
    return redirect(location)

@app.route('/redirect/', methods=['HEAD', 'GET', 'POST'])
def redirect():
    ar = Auth_Redirect()

    location = ar.auth_redirect(request)

    return redirect(location)

@app.route('/box/', methods=['HEAD', 'GET', 'POST'])
def redirect():
    ar = Auth_Redirect()

    location = ar.auth_redirect(request)

    return redirect(location)

@app.route('/jwks/', methods=['GET'])
def get_jwks():
    with open('keys/public.jwk.json') as f:
        data = json.load(f)

    print(data)
    return jsonify({ "keys" : [ data ] })

@app.route('/embed/<launch_id>/', methods=['GET'])
def embed(launch_id):
    """tool_conf = ToolConfJsonFile(get_lti_config_path())
    print(f"tool_conf: {tool_conf}")
    flask_request = FlaskRequest()
    launch_data_storage = get_launch_data_storage()
    print(f"launch_data_storage: {launch_data_storage}")
    message_launch = ExtendedFlaskMessageLaunch.from_cache(launch_id, flask_request, tool_conf,
                                                           launch_data_storage=launch_data_storage)

    print(f"message_launch: {message_launch}")

    if not message_launch.is_deep_link_launch():
        raise FORBIDDEN('Must be a deep link!')

    launch_url = config.tool_config['APP_URL'] + "/launch/"

    args = request.args

    print(f"launch_url = {launch_url} args = {args}")

    count = int(args['count'])

    resources = []

    for x in range(count):
        resource = DeepLinkResource()

        resource.set_url(launch_url) \
            .set_custom_params({'box_file_id': args.get("fileId" + str(x))}) \
            .set_title(args.get("filename" + str(x)))

        resources.append(resource)

    html = message_launch.get_deep_link().output_response_form(resources)
    print(f"html is {html}")"""
    return #html

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

if __name__ == '__main__':
    
    port = int(os.environ.get('PORT', 55000))
    app.run(host='0.0.0.0', port=port)
