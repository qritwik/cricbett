import json
import os
import sys
from datetime import datetime

import falcon
import yaml
from django.contrib.auth import authenticate
from django.core.wsgi import get_wsgi_application
from auth_service.utils import helper
from clients.logger_client import LoggerClient


sys.path.append(os.pardir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'cricbett_db.settings'
get_wsgi_application()

# Todo: Create a GitHub Repo and upload the code


class SendOtp(object):
    """
    This class handles the POST requests for sending OTP to phone number.
    """

    def __init__(self, logger):
        """
        :param logger: Logger client used for logging.
        """
        self.logger = logger

    def on_post(self, req, resp):
        """
        This method handles the POST requests for sending OTP.

        Parameters:
        req (object) : request object
        resp (object) : response object

        Returns:
        None
        """
        try:
            # Parse JSON request body
            data = json.loads(req.stream.read())

            # Check if phone number is passed in request
            phone = data.get('phone')
            if phone is None:
                self.logger.error(f"Phone not present in Send OTP Request. Key phone is required!")
                raise ValueError('key phone is required')

            self.logger.info(f"Received Send OTP Request for phone:{phone}")

            # Send OTP to phone number
            # otp = helper.send_otp_to_phone(phone=phone, logger=self.logger)
            otp = "1234"

            # Authenticate user with phone number as username and password
            player = authenticate(phone=phone, password=phone)
            if player is None:
                self.logger.info("Player is none")
                # Create new user and set OTP
                player = self.create_new_user(phone, otp)
                player.set_password(phone)
                player.save()
                resp.status = falcon.HTTP_201
                resp.text = json.dumps({
                    'user_type': 'new_user',
                    'message': 'otp sent successfully',
                    'phone': phone
                })
                self.logger.info(f"New user:{phone} Sent OTP to phone! Created a new user")
            else:
                self.logger.info("Player is old")
                # Update OTP for existing user
                player.otp = str(otp)
                player.save()
                resp.status = falcon.HTTP_200
                resp.text = json.dumps({
                    'user_type': 'old_user',
                    'message': 'otp sent successfully',
                    'phone': phone
                })
                self.logger.info(f"Existing user:{phone} Sent OTP to phone!")

        except ValueError as e:
            self.logger.error(f"{str(e)}")
            resp.status = falcon.HTTP_404
            resp.text = json.dumps({
                'message': str(e)
            })
        except Exception as e:
            self.logger.error(f"{str(e)}")
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({
                'message': 'internal server error',
                'error': str(e)
            })

    @staticmethod
    def create_new_user(phone, otp):
        """
        This method creates a new player instance with provided phone number and OTP.

        :param phone: player's phone number
        :param otp: OTP for player
        :return: player instance
        """
        from db.models import Player
        player = Player.objects.create(
            phone=phone,
            otp=str(otp)
        )
        return player


class VerifyOtp(object):
    """
    Endpoint for verifying OTP.
    """

    def __init__(self, logger):
        """
        :param logger: Logger client used for logging.
        """
        self.logger = logger

    def on_post(self, req, resp):
        """
        This method handles the POST requests for verifying OTP.

        Parameters:
        req (object) : request object
        resp (object) : response object

        Returns:
        None
        """
        try:
            # Parse the request body
            data = json.loads(req.stream.read())

            # Check if phone number is present in the request
            phone = data.get('phone')
            if phone is None:
                self.logger.error(f"Phone not present in Verify OTP Request. Key phone is required!")
                raise ValueError('key phone is required')

            # Check if OTP is present in the request
            otp = data.get('otp')
            if otp is None:
                self.logger.error(f"OTP not present in Verify OTP Request. Key otp is required!")
                raise ValueError('key otp is required')

            self.logger.info(f"Received Verify OTP Request for phone:{phone}")

            # Authenticate player using phone_number
            player = authenticate(phone=phone, password=phone)

            # Player does not exist
            if player is None:
                self.logger.error(f"Verify OTP: Phone does not exists")
                raise ValueError('phone does not exists')

            self.check_otp(player, otp, phone, resp)

        except ValueError as e:
            self.logger.error(f"{str(e)}")
            resp.status = falcon.HTTP_404
            resp.text = json.dumps({
                'message': str(e),
                'phone': phone,
                'token': None
            })
        except Exception as e:
            self.logger.error(f"{str(e)}")
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({
                'message': 'internal server error',
                'error': str(e)
            })

    def check_otp(self, player, otp, phone, resp):
        """
        Check if the OTP in the request payload matches against the OTP in the Player DB
        It checks if player's token already exists and it is active. If not active, it
        delets the existing token and generates a new token.

        Parameters:
        player (object): player object from the database
        otp (str): OTP from the request payload
        phone (str): phone number of the player
        resp (object): response object from Falcon

        Returns:
        None
        """
        try:
            # Check if OTP from request matches OTP in player DB
            if player.otp == otp:
                token_id = player.token.token_id if player.token else None
                print(f'token:{token_id}')

                # Check if token does not already exist and invalid
                if not helper.is_token_valid(token_id):
                    token_id = helper.generate_token_id(phone)
                    token = self.create_token_obj(token_id)
                    player.token = token

                # Create wallet for the user if it doesn't exist
                if player.wallet is None:
                    walletObj = self.create_wallet_obj()
                    player.wallet = walletObj

                # Set OTP to None and update player in the DB
                player.otp = None
                player.is_phone_verified = True
                player.save()
                resp.status = falcon.HTTP_202
                resp.text = json.dumps({
                    'message': 'otp verified',
                    'phone': phone,
                    'token': str(token_id)
                })
                self.logger.info(f"OTP Verified Successfully!")
                return
            else:
                # Input OTP does not match with OTP in DB
                resp.status = falcon.HTTP_401
                resp.text = json.dumps({
                    'message': 'invalid otp',
                    'phone': phone,
                    'token': None
                })
                self.logger.warning(f"OTP Doesn't Match. Try Sending OTP Again!")
                return
        except Exception as e:
            self.logger.error(f"Error while verifying OTP: {e}")
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({
                'message': 'internal server error',
                'phone': phone,
                'token': None
            })

    def create_token_obj(self, token_id):
        """
        Create a new token object
        """
        from db.models import Token
        try:
            token = Token.objects.create(
                token_id=token_id,
                token_creation_datetime=datetime.now(),
                token_expiry_datetime=datetime.now(),
                token_status='ACTIVE'
            )
            return token
        except Exception as e:
            self.logger.error(f"Error while creating token: {e}")
            return None

    def create_wallet_obj(self):
        """
        Create a new wallet object
        """
        from db.models import Wallet
        try:
            wallet = Wallet.objects.create(
                wallet_amount=0
            )
            return wallet
        except Exception as e:
            self.logger.error(f"Error while creating wallet: {e}")
            return None


class HealthCheck(object):
    """
    HealthCheck class, it is a Falcon web framework's resource class.
    """

    def on_get(self, req, resp):
        """
        Handles GET requests to the endpoint
        """
        resp.status = falcon.HTTP_200
        resp.text = json.dumps("OK")


def initialize_and_start_service(cfg, logger):
    app = falcon.App()

    sendOtp = SendOtp(logger=logger)
    app.add_route('/send_otp', sendOtp)
    app.add_route('/resend_otp', sendOtp)

    verifyOtp = VerifyOtp(logger=logger)
    app.add_route('/verify_otp', verifyOtp)

    healthCheck = HealthCheck()
    app.add_route('/healthcheck', healthCheck)

    logger.info("Cricbett-Auth API is live now!")

    return app


# Load the configuration file
config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config/auth_config.yaml")

# Open and read the configuration file into the config variable
with open(config_file, 'r') as cf:
    config = yaml.safe_load(cf)

# Setup LoggingClient by passing the config
logger_client = LoggerClient("cricbett-auth", config)

# Initialize and start the service using the config
api = initialize_and_start_service(config, logger_client)
