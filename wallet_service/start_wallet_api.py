import json
import os
import sys

import falcon
import yaml
from django.core.wsgi import get_wsgi_application

from auth_service.utils.helper import validate_token
from clients.logger_client import LoggerClient

sys.path.append(os.pardir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'cricbett_db.settings'
get_wsgi_application()

from db.models import Player


class WalletEndpoint(object):

    def __init__(self, logger):
        """
        Initializes the service with a logger.
        """
        self.logger = logger

    @validate_token
    def on_post(self, req, resp, **kwargs):
        """
        Handle POST requests to update/edit player's pancard information
        """
        # Parse the request body
        try:
            # Read the request body and decode it as a JSON object
            data = json.loads(req.stream.read().decode("utf-8"))
        except Exception as e:
            # If the request body cannot be decoded, log the error and return a HTTP 400 response
            self.logger.error(f"Error decoding request body: {e}")
            resp.status = falcon.HTTP_400
            resp.text = json.dumps({"error": "Invalid request body"})
            return

        try:
            # Check if pancard is present in the request
            pancard = data.get('pancard')
            if pancard is None or pancard == "":
                # If pancard is not present, log the error and return an HTTP 400 response
                self.logger.error(f"Pancard not present in Request. Key pancard is required!")
                resp.status = falcon.HTTP_400
                resp.text = json.dumps({"error": "key pancard is required"})
                return

            # Retrieve the token from the keyword arguments
            token = kwargs.get("token")

            # Try to retrieve the player details using the token
            try:
                player = Player.objects.filter(token__token_id=token).first()
            except Exception as e:
                # If an error occurs while retrieving the player details, log the error and return a HTTP 500 response
                self.logger.error(f"Error retrieving player details with token {token}. Error: {e}")
                resp.status = falcon.HTTP_500
                resp.text = json.dumps({"error": "An error occurred while retrieving player details"})
                return

            # If the player is not found, return a bad request response
            if not player:
                self.logger.error(f"Player with token {token} not found")
                resp.status = falcon.HTTP_400
                resp.text = json.dumps({"error": "Invalid token"})
                return

            # Update the pancard information for the player
            player_wallet = player.wallet
            player_wallet.pancard = pancard
            player_wallet.pancard_verified = False
            player_wallet.save()

        except KeyError as e:
            self.logger.error(f"Missing required field in request body: {e}")
            resp.status = falcon.HTTP_400
            resp.text = {"message": f"Missing required field: {e} in request body"}
            return
        except Exception as e:
            self.logger.error(f"Error: {e}")
            resp.status = falcon.HTTP_500
            resp.text = {"message": f"Error: {e}"}
            return

        # Log the updated pancard information and return a HTTP 202 response
        self.logger.info(f"Updated pancard for wallet:{player_wallet.wallet_id}")
        resp.status = falcon.HTTP_202
        resp.text = json.dumps({"message": "Pancard Details Updated"})

    @validate_token
    def on_get(self, req, resp, **kwargs):
        """
        Handles the GET request for retrieving the wallet information of a player.

        :param req: Falcon request object
        :param resp: Falcon response object
        :param kwargs: Keyword arguments passed in the request
        """
        # Retrieve the token from the keyword arguments
        token = kwargs.get("token")

        # Try to retrieve the player details using the token
        try:
            player = Player.objects.filter(token__token_id=token).first()
        except Exception as e:
            self.logger.error(f"MyGameService: Error retrieving player details with token {token}. Error: {e}")
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": "An error occurred while retrieving player details"})
            return

        # If the player is not found, return a bad request response
        if not player:
            self.logger.error(f"MyGameService: Player with token {token} not found")
            resp.status = falcon.HTTP_400
            resp.text = json.dumps({"error": "Invalid token"})
            return

        # Retrieve the wallet information
        try:
            response = self.get_wallet_response(player)
        except Exception as e:
            self.logger.error(f"MyGameService: Error retrieving wallet information for player with id {player.id}. Error: {e}")
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": "An error occurred while retrieving wallet information"})
            return

        # Return the wallet information in a JSON format
        resp.status = falcon.HTTP_200
        resp.text = json.dumps(response)

    @staticmethod
    def get_wallet_response(player):
        """
        Returns the wallet information for a player.

        :param player: Player object
        :return: Dictionary with the player's wallet information
        """
        player_wallet = player.wallet
        return {
            "phone": player.phone,
            "email": player.email,
            "name": player.name,
            "pancard": player_wallet.pancard,
            "wallet_amount": str(player_wallet.wallet_amount),
            "pancard_verified": player_wallet.pancard_verified
        }


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

    # GET /wallet
    walletEndpoint = WalletEndpoint(logger=logger)
    app.add_route('/wallet', walletEndpoint)

    healthCheck = HealthCheck()
    app.add_route('/healthcheck', healthCheck)

    logger.info("Cricbett-Wallet API is live now!")

    return app


# Load the configuration file
config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config/wallet_config.yaml")

# Open and read the configuration file into the config variable
with open(config_file, 'r') as cf:
    config = yaml.safe_load(cf)

# Setup LoggingClient by passing the config
logger_client = LoggerClient("cricbett-wallet", config)

# Initialize and start the service using the config
api = initialize_and_start_service(config, logger_client)
