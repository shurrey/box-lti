import functions_framework
from google.cloud import logging

import base64
import json
import os
from pprint import pformat
from urllib import parse as urlparse
import uuid

from flask import redirect
import jwt


import box
from db.db import DB
from jwk.jwk import JWK_Util

class Launch:

    def __init__(self) -> None:
        # Configure Logger
        logging_client = logging.Client()
        self.logger = logging_client.logger('lti_launch')

        self.db = DB()

        self.config = {}
        self.cache = {}
        self.user = {}
    
    def process_launch(self, id_token):
        self.logger.log_text(f"LTIValidation->process_launch: id_token: {id_token}")

        jwt_parts = id_token.split(".")
        self.logger.log_text(f"LTIValidation->process_launch: jwt_parts: {jwt_parts}")
        self.logger.log_text(f"LTIValidation->process_launch: jwt_parts: header {jwt_parts[0]}")
        self.logger.log_text(f"LTIValidation->process_launch: jwt_parts: body {jwt_parts[1]}")
        self.logger.log_text(f"LTIValidation->process_launch: jwt_parts: {jwt_parts[2]}")

        jwt_header = json.loads(self.decode_jwt_parts(jwt_parts[0]))
        self.logger.log_text(f"LTIValidation->process_launch: jwt_header: " + pformat(jwt_header))

        jwt_body = json.loads(self.decode_jwt_parts(jwt_parts[1]))
        self.logger.log_text(f"LTIValidation->process_launch: jwt_body: " + pformat(jwt_body))

        aud = ""
        if isinstance(jwt_body['aud'], list):
            aud = jwt_body['aud'][0]
        else:
            aud = jwt_body['aud']

        self.logger.log_text(f"LTIValidation->process_launch: aud: {aud}")
        self.logger.log_text(f"LTIValidation->process_launch: client_id: {self.client_id}")
        
        if aud != self.client_id:
            self.logger.log_text(f"LTIValidation->process_launch: Invalid client Id {aud} {self.client_id}", severity="ERROR")
            return 'Invalid client_id', 401
            

        self.logger.log_text(f"LTIValidation->process_launch: get public key: {jwt_header['kid']}")
        
        try:
            jwks_client = jwt.PyJWKClient(self.jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)
            data = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                options={"verify_exp": False},
            )
            self.logger.log_text(f"LTIValidation->process_launch: post_validation_data: {data}")

            return data, None

        except Exception as e:
            self.logger.log_text(f"LTIValidation->process_launch: Exception: {e}", severity="ERROR")
            return f"LTIValidation->process_launch: Exception: {e}", 500
    
    def get_lms_data(self,launch_data):

        lms_data = {
            "deployment_id" : launch_data["https://purl.imsglobal.org/spec/lti/claim/deployment_id"],
            "system_guid" : launch_data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"]["guid"],
            "client_id" : launch_data["aud"],
            "issuer" : launch_data["iss"],
            "lms" : launch_data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"]["name"],
            "url" : launch_data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"]["url"],
            "contact_email" : launch_data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"]["contact_email"],
            "version" : launch_data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"]["version"],
            "user_id" : launch_data["sub"],
            "user_role" : [launch_data["https://purl.imsglobal.org/spec/lti/claim/roles"]],
            "message_type" : launch_data["https://purl.imsglobal.org/spec/lti/claim/message_type"]
        }

        return lms_data
    
    def get_nrps_data(self,nrps_url,access_token):
        
        headers = {
            'Authorization' : 'Bearer ' + access_token,
            'Accepts' : self.NRPS_CONTENT_TYPE
        }

        #response = requests.get(nrps_url, headers=headers)
    
def lti_launch(self,request):
    
    try:
        
        launch_params = request.form
        
        self.logger.log_text(f"launch params {launch_params}")

        id_token = launch_params['id_token']
        self.logger.log_text(f"id_token {id_token}")
        state = launch_params['state']
        self.logger.log_text(f"state {state}")
        
        cache = db.get_cache_data(state)
        self.logger.log_text(f"cache {cache}")

        if not cache:
            retval='Invalid state parameter. You no hax0r!'
            self.logger.log_text(f"Error: {retval}")
            return retval, 401
        
        self.db.set_params(cache["client_id"], cache["lti_deployment_id"])

        config = self.db.get_config()

        if not config:
            retval='Invalid configuration. You no hax0r!'
            self.logger.log_text(f"Error: {retval}")
            return retval, 401

        """self.logger.log_text(f"client ID {config['client_id']} jwks_url {config['jwks_url']}")

        lti = jwk.lti_util(logger,config['client_id'],config['jwks_url'])
        
        self.logger.log_text("get json")
        launch_data = lti.process_launch(id_token)
        self.logger.log_text(f"launch_data {launch_data}")

        lms_data = lti.get_lms_data(launch_data)
        self.logger.log_text(f"lms_data {lms_data}")

        user = self.db.get_user(launch_data['sub'])

        box = box_util.box_util(logger)

        self.logger.log_text(f"if not user")

        if user is None:
            self.logger.log_text(f"call oauth2")
            auth_url, csrf_token = box.oauth2()

            self.logger.log_text(f"auth_url {auth_url} csrf_token {csrf_token}")

            self.db.create_document('cache', csrf_token, launch_data)

            return redirect(auth_url)
        
        launch_id =launch_data['nonce']
        nonce = uuid.uuid4().hex
        
        self.db.create_document('cache', launch_id, launch_data)"""
        
        return f"/box?launch_id={launch_id}&nonce={nonce}"

    except Exception as e:
        self.logger.log_text(f"LTIValidation: Error validating lti launch - {e}", severity="ERROR")
        return str(e), 500
