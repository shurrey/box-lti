import functions_framework
from google.cloud import logging

import json
import os
import uuid

from pprint import pformat
from flask import redirect

from db.db import DB

class Login:
    
    def __init__(self) -> None:
        
        logging_client = logging.Client()
        self.logger = logging_client.logger('oidclogin')
        
        self.db = DB()

        self.config = {}

    def build_url(self, login_params,config,state,nonce):
        
        oidcparams = f"?scope=openid"
        oidcparams += f"&response_type=id_token"
        oidcparams += f"&response_mode=form_post"
        oidcparams += f"&prompt=none"
        oidcparams += f"&client_id={login_params['client_id']}"
        oidcparams += f"&redirect_uri={login_params['target_link_uri']}"
        oidcparams += f"&state={state}"
        oidcparams += f"&nonce={nonce}"
        oidcparams += f"&login_hint={login_params['login_hint']}"

        if "lti_message_hint" in login_params:
            oidcparams += f"&lti_message_hint={login_params['lti_message_hint']}"
        
        return f"{config['auth_login_url']}{oidcparams}"

    def oidc_login(self, request):
            
        login_params = request.args
        
        self.logger.log_text(f"oidc_login->lambda_handler: login_params={login_params}")

        self.db.set_params(login_params['client_id'], login_params['lti_deployment_id'])

        config = self.db.get_config()
        
        if config is not None:
            
            self.logger.log_text(f"oidc_login->lambda_handler: set state")

            state = uuid.uuid4()
            nonce = uuid.uuid4().hex
            
            self.logger.log_text(f"oidc_login->lambda_handler: state={state} nonce={nonce}")
            
            location = self.build_url(login_params,config,state,nonce)
            
            self.logger.log_text(f"oidc_login->lambda_handler: location={location}")

            cache_value = { 
                "iss" : login_params['iss'],
                "lti_deployment_id" : login_params['lti_deployment_id'],
                "client_id" : login_params['client_id'],
                "login_hint" : login_params["login_hint"],
                "target_link_uri" : login_params["target_link_uri"],
                "lti_message_hint" : login_params["lti_message_hint"],
                "lti_storage_target" : login_params["lti_storage_target"],
            }

            self.db.cache(state,cache_value)
            
            self.logger.log_text(f"state = {state} cache_value = {cache_value}")

            self.logger.log_text(f"oidc_login->lambda_handler: return")
        
            return location, None
            
        else:
            
            message = f"Invalid deployment ID, client ID, or issuer"
            self.logger.log_text(f"oidc_login->lambda_handler: 400 {message}", severity="ERROR")
            return json.dumps(message), 404