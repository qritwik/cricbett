import os
import random
import sys
import time

import falcon
import jwt
import requests
from django.core.wsgi import get_wsgi_application

os.chdir(os.pardir)
sys.path.append(os.pardir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'cricbett_db.settings'
get_wsgi_application()

secret_key = 'ritwik1804'
api_key = 'd0c74322-6e38-11ed-9c12-0200cd936042'


def send_otp_to_phone(phone, logger):
    try:
        otp = random.randint(1000, 9999)
        url = f'https://2factor.in/API/V1/{api_key}/SMS/{phone}/{otp}/HOPA1'
        requests.get(url=url)
        logger.info(f"OTP Sent to Phone {phone}")
        return otp
    except Exception as e:
        raise e


def generate_token_id(phone):
    payload = {
        'phone': phone,
        'creation_time': time.time()
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token


def generate_token_from_payload(payload):
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token


def is_token_valid(token_id):
    try:
        if token_id is None:
            return False

        from db.models import Token
        token = Token.objects.get(token_id=token_id)
        token_status = token.token_status.upper()
        return token_status == 'ACTIVE'
    except:
        return False


def validate_token(func):
    def wrapper(self, req, resp, *args, **kwargs):
        try:
            token = req.headers.get('Authorization'.upper())
            if token == "":
                raise falcon.HTTPUnauthorized(description='Token not present in authorization header')
            if token is not None:
                if is_token_valid(token):
                    return func(self, req, resp, token=token, *args, **kwargs)
                else:
                    raise falcon.HTTPUnauthorized(description='Invalid Token')
            else:
                raise falcon.HTTPUnauthorized(description='Authorization header not present in request header')
        except Exception as e:
            raise e

    return wrapper
