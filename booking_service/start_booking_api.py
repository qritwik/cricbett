import json
import os
import sys
from datetime import datetime

import falcon
import pytz
import yaml
from django.core.wsgi import get_wsgi_application

from auth_service.utils.helper import validate_token
from clients.logger_client import LoggerClient

sys.path.append(os.pardir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'cricbett_db.settings'
get_wsgi_application()

from db.models import Player, Game, Payment, Booking


class BookingEndpoint:
    """
    Falcon endpoint for creating a booking object
    """

    def __init__(self, logger):
        """
        Initializes the service with a logger.
        """
        self.logger = logger

    @validate_token
    def on_post(self, req, resp, **kwargs):
        """
        Handle the POST request for creating a booking object
        {
            "game": "1",
            "player": "8709996580",
            "payment_status": "successful",
            "razorpay_payment_id": "12345",
            "razorpay_order_id": "12345",
            "razorpay_signature": "12345",
            "player_bid_price": 100,
            "player_bid_team": "India",
            "player_bid_multiplier": 1.8,
            "player_won_price": 180
        }
        """
        # Read and parse the request body as a JSON object
        try:
            request = json.loads(req.stream.read())
        except json.JSONDecodeError as e:
            self.logger.error(f"Error while decoding request body: {e}")
            resp.status = falcon.HTTP_400
            resp.media = {"message": "Invalid request body"}
            return

        try:
            # Get player and game objects
            player_phone = request['player']
            player = Player.objects.get(phone=player_phone)
            game_id = request['game']
            game = Game.objects.get(game_id=game_id)

            # Check if game_status is not UPCOMING
            if game.game_status != "UPCOMING":
                self.logger.error(
                    f"Bookings can only be made for upcoming games. The current game status is {game.game_status}.")
                resp.status = falcon.HTTP_400
                resp.media = {
                    "message": f"Sorry, bookings can only be made for upcoming games. The current game status is {game.game_status}."}
                return

            # Check if player bid team in request is one from valid teams.
            player_bid_team = str(request['player_bid_team']).upper()
            teams = [game.match.first_team, game.match.second_team]
            if player_bid_team not in teams:
                resp.status = falcon.HTTP_400
                resp.text = json.dumps(
                    {"msg": f"Invalid player_bid_team value in request. Must be one from {str(teams)}"})
                return

            # If booking already exists for player and game, return error
            if Booking.objects.filter(player=player, game=game).exists():
                self.logger.error(
                    f"Booking for game:{game_id} already exists for player:{player_phone}.")
                resp.status = falcon.HTTP_400
                resp.media = {
                    "code": "booking_already_exists",
                    "message": f"Booking for game:{game_id} already exists for player:{player_phone}"}
                return

            # If valid payment status create payment object
            if self.is_valid_request(request):
                payment = self.create_payment_obj(request)
            else:
                self.logger.error(f"Not a valid payment_status in request body.")
                resp.status = falcon.HTTP_400
                resp.media = {
                    "code": "payment_status_not_valid",
                    "message": f"Not a valid payment_status in request body. Can be either 'SUCCESSFUL', 'FAILED', 'PENDING'"}
                return

            # Get payment id and status
            payment_id = payment.id
            payment_status = str(payment.payment_status).upper()

            # If payment status is not successful, return error
            if payment_status != 'SUCCESSFUL':
                self.logger.error(
                    f"Payment status is not SUCCESSFUL for Payment:{payment_id}. Hence booking can't be made.")
                resp.status = falcon.HTTP_400
                resp.media = {
                    "code": "payment_not_success",
                    "message": f"Payment status is not SUCCESSFUL for Payment:{payment_id}. Hence booking can't be made."}
                return

            # If payment has already been used for an active booking, return error (Just to be double sure)
            if Booking.objects.filter(payment=payment).exists():
                self.logger.error(f"Payment:{payment_id} already used for some active booking.")
                resp.status = falcon.HTTP_400
                resp.media = {"message": f"Payment:{payment_id} already used for some active booking."}
                return

            # If all checks pass, create a booking object
            booking = self.create_booking_obj(request, player, game, payment)
            resp.status = falcon.HTTP_201
            resp.media = {"booking_id": booking.booking_id}
            self.logger.info(f"Booking object created for booking_id:{booking.booking_id}")

        except KeyError as e:
            self.logger.error(f"Missing required field in request body: {e}")
            resp.status = falcon.HTTP_400
            resp.media = {"message": f"Missing required field: {e} in request body"}
            return
        except Exception as e:
            self.logger.error(f"Error while creating booking object: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {"message": f"Error while creating booking object {e}"}
            return

        # Return the payment ID as the response
        resp.status = falcon.HTTP_202
        resp.media = {
            "booking_id": booking.booking_id,
            "game_id": game_id,
            "game_type": game.game_type,
            "current_game_status": game.game_status,
            "match_name": game.match.match_name,
            "match_type": game.match.match_type,
            "amound_paid": booking.player_bid_price,
            "winning_amount": booking.player_won_price,
            "team_choosed": booking.player_bid_team
        }
        self.logger.info(f"Booking object created for booking_id:{booking.booking_id}")

    @staticmethod
    def is_valid_request(request):
        # Check if payment_status in request body in one from valid options.
        payment_status = str(request['payment_status']).upper()
        valid_status = ['SUCCESSFUL', 'FAILED', 'PENDING']
        return payment_status in valid_status

    @staticmethod
    def create_payment_obj(request):
        """
        Create a payment object
        """
        tz = pytz.timezone('Asia/Kolkata')
        payment = Payment.objects.create(
            amount=request['player_bid_price'],
            payment_status=str(request['payment_status']).upper(),
            payment_datetime=datetime.now(tz=tz),
            razorpay_payment_id=request['razorpay_payment_id'],
            razorpay_order_id=request['razorpay_order_id'],
            razorpay_signature=request['razorpay_signature']
        )
        return payment

    @staticmethod
    def create_booking_obj(request, player, game, payment):
        """
        Create a payment object
        """
        tz = pytz.timezone('Asia/Kolkata')
        booking = Booking.objects.create(
            player=player,
            game=game,
            player_bid_price=request['player_bid_price'],
            player_bid_team=str(request['player_bid_team']).upper(),
            player_bid_multiplier=request['player_bid_multiplier'],
            player_won_price=request['player_won_price'],
            booking_datetime=datetime.now(tz=tz),
            payment=payment
        )
        return booking


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

    bookingEndpoint = BookingEndpoint(logger)
    app.add_route('/booking', bookingEndpoint)

    healthCheck = HealthCheck()
    app.add_route('/healthcheck', healthCheck)

    logger.info("Cricbett-Booking API is live now!")

    return app


# Load the configuration file
config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config/booking_config.yaml")

# Open and read the configuration file into the config variable
with open(config_file, 'r') as cf:
    config = yaml.safe_load(cf)

# Setup LoggingClient by passing the config
logger_client = LoggerClient("cricbett-booking", config)

# Initialize and start the service using the config
api = initialize_and_start_service(config, logger_client)
