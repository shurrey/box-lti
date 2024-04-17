import base64
import json
import jwk
import jwt
import string
from google.cloud import logging
from google-cloud-secret-manager import secretmanager
import google_crc32c
import os
from pprint import pformat
from urllib import parse as urlparse
import urllib3
import secrets
import uuid
import time
import requests

class JWK_Util:

    def __init__(self, logger, client_id, jwks_url):
        self.logger = logger
        self.client_id = client_id
        self.jwks_url = jwks_url

        self.http = urllib3.PoolManager()

        self.NRPS_CONTENT_TYPE = 'application/vnd.ims.lti-nrps.v2.membershipcontainer+json'
        self.NRPS_SCOPE = 'https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly'

    def getJwks(self):
        client = secretmanager.SecretManagerServiceClient()

        # Build the resource name of the secret version.
        name = f"projects/821305823385/secrets/box-lti-public-key/versions/1"
        self.logger.log_text(f"name is {name}")

        # Access the secret version.
        secret = client.access_secret_version(request={"name": name})
        self.logger.log_text(f"secret is {secret}")

        # Verify payload checksum.
        crc32c = google_crc32c.Checksum()
        self.logger.log_text(f"crc32c is {crc32c}")
        crc32c.update(secret.payload.data)
        if secret.payload.data_crc32c != int(crc32c.hexdigest(), 16):
                print("Data corruption detected.")
                return secret

        public_pem = secret.payload.data.decode("UTF-8")

        key = jwk.JWK.from_pem(public_pem.encode('utf-8'))
        public_jwk = json.loads(key.export_public())
        public_jwk['alg'] = 'RS256'
        public_jwk['use'] = 'sig'

        self.logger.log_text(f"key {key} public_jwk {public_jwk}")

        jwks = {
                "keys" : [
                        public_jwk
                ]
        }

        headers = {"Content-Type": "application/json"}


        return (json.dumps(jwks), 200, headers)
    
    def decode_jwt_parts(self, part):
        self.logger.log_text(f"LTIValidation->decode_jwt_parts: part: {part}")
        s = str(part).strip()
        self.logger.log_text(f"LTIValidation->decode_jwt_parts: s: {s}")

        remainder = len(part) % 4
        if remainder > 0:
            padlen = 4 - remainder
            part = part + ('=' * padlen)
        if hasattr(str, 'maketrans'):
            tmp = part.translate(str.maketrans('-_', '+/'))
            return base64.b64decode(tmp).decode("utf-8")
        else:
            tmp = str(part).translate(string.maketrans('-_', '+/'))
            return base64.b64decode(tmp)

    def get_kid(self):

        public_key=self.sec_svc.get_key(True)

        key = jwk.JWK.from_pem(public_key.encode('utf-8'))
        public_jwk = json.loads(key.export_public())
        
        return public_jwk['kid']
    
    def build_jwt_for_token(self, token_url):
        sec_svc = secrets.secrets(self.logger)

        private_key=sec_svc.get_key()

        nonce = uuid.uuid4().hex

        now = int(time.time())
        exp = now + 300

        jwt_body = {
            "iss" : "box.com",
            "sub": self.client_id,
            "aud": [ token_url ],
            "jti": nonce,
            "exp": exp,
            "iat": now
        } 

        encoded = jwt.encode(jwt_body, private_key, algorithm="RS256")
        print(encoded)

        return encoded
    
    def get_lti_token(self, token_url):

        jwt_token = self.build_jwt_for_token(token_url)

        headers = {
            'Content-Type' : 'application/x-www-form-urlencoded'
        }

        params = {
            'grant_type' : 'client_credentials',
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'client_assertion' : jwt_token,
            'scope' : self.NRPS_SCOPE
        }

        body = urlparse.quote(json.dumps(params, ensure_ascii=False).encode('utf-8'))

        res = requests.post(token_url, data=body, headers=headers)

        self.logger.log_text(f"res is {res.text}")

        return res