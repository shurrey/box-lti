import functions_framework
from google.cloud import logging

import base64
import json
import os
from pprint import pformat
from urllib import parse as urlparse
import uuid

from flask import redirect, request

from box.box import Box
from db.db import DB

class Auth_Redirect:
    
    def __init__(self) -> None:
        
        # Configure Logger
        logging_client = logging.Client()
        self.logger = logging_client.logger('lti_launch')

        self.db = DB()

        self.config = {}
        self.launch_data = {}
        self.user = {}


    def auth_redirect(self, request):

        args = request.args
        
        csrf_token = args.get('state')
        auth_code = args.get('code')

        launch_params = self.db.get_cache_data(csrf_token)

        self.logger.log_text(f"launch params {launch_params}")

        box = Box()

        user = box.oauth2(auth_code)

        self.db.add_user(user,launch_params)

        launch_id =launch_params['nonce']
        nonce = uuid.uuid4().hex
        
        self.db.create_document('cache', launch_id, launch_params)
        
        return (f"/box?launch_id={launch_id}&nonce={nonce}")