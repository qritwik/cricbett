import json
import os
import sys

import falcon
import yaml
from django.core.wsgi import get_wsgi_application

from auth_service.utils.helper import validate_token
from clients.logger_client import LoggerClient
from clients.utils import convert_utc_into_ist

sys.path.append(os.pardir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'cricbett_db.settings'
get_wsgi_application()

from db.models import Match
from db.models import Player


class MatchService(object):
    """
    A Falcon service class that handles GET requests and filters a list of matches based on query parameters "match_type" and "match_status".
    GET /matches?&match_type=cricket&match_status=upcoming
    [
        {
            "match_name": "2nd ODI, IND v NZ",
            "match_status": "COMPLETED",
            "match_start_datetime": "2023-02-11T04:00:00Z",
            "match_end_datetime": null,
            "match_venue": "Raipur",
            "match_type": "CRICKET",
            "first_team": "INDIA",
            "second_team": "NEW ZEALAND",
            "match_id": 1
        }
    ]
    """

    def __init__(self, logger):
        """
        Initialize the MatchService class.

        :param logger: Logger client used for logging.
        """
        self.logger = logger

    @validate_token
    def on_get(self, req, resp, **kwargs):
        """
        Handles GET requests to the endpoint and filters the matches based on query parameters "match_type" and "match_status".
        If no query parameters are provided, it returns all the matches.

        :param req: Falcon request object.
        :param resp: Falcon response object.
        """
        try:
            match_type = req.params.get("match_type", "").upper()
            match_status = req.params.get("match_status", "").upper()

            matches = Match.objects.filter(
                match_type__contains=match_type, match_status__contains=match_status
            )
            response = []
            for match in matches:
                response.append(self.get_match_response(match))

            resp.status = falcon.HTTP_202
            resp.text = json.dumps(response)
            self.logger.info(
                f"MatchService: Successfully retrieved matches with match_type={match_type} and match_status={match_status}")
        except Exception as e:
            resp.status = falcon.HTTP_400
            resp.text = json.dumps({"error": str(e)})
            self.logger.error(f"MatchService: Failed to retrieve matches: {e}")

    @staticmethod
    def get_match_response(match):
        match_start_datetime = convert_utc_into_ist(str(match.match_start_datetime))
        return {
            "match_id": str(match.match_id),
            "match_name": str(match.match_name),
            "match_status": str(match.match_status),
            "match_start_datetime": str(match_start_datetime),
            "match_venue": str(match.match_venue),
            "match_type": str(match.match_type),
            "first_team": str(match.first_team),
            "second_team": str(match.second_team)
        }


class MyGameService(object):
    """
    This class is responsible for handling the requests for getting the bookings related to a player.
    GET /my_games?game_status=live&match_type=football
    """

    def __init__(self, logger):
        """
        Initializes the service with a logger.

        :param logger: Logger client used for logging.
        """
        self.logger = logger

    @validate_token
    def on_get(self, req, resp, **kwargs):
        """
        Handles the GET request for getting the bookings related to a player.
        """
        token = kwargs.get("token")
        match_type = req.params.get("match_type", "").upper()
        game_status = req.params.get("game_status", "").upper()

        player = Player.objects.filter(token__token_id=token).first()
        if not player:
            self.logger.error(f"MyGameService: Player with token {token} not found")
            resp.status = falcon.HTTP_400
            resp.text = json.dumps({"error": "Invalid token"})
            return

        player_booking_set = player.booking_set.filter(
            game__game_status__contains=game_status,
            game__match__match_type__contains=match_type
        )

        my_bookings = {
            "player_id": player.player_id,
            "player_phone": player.phone,
            "player_games": [
                self.get_response_template(player_booking) for player_booking in player_booking_set
            ]
        }

        resp.status = falcon.HTTP_202
        resp.text = json.dumps(my_bookings)

    @staticmethod
    def get_response_template(player_booking):
        """
        Creates the response template for the contest details.
        """
        if player_booking.game.game_type == "WIN_PREDICT":
            game_start_time = convert_utc_into_ist(str(player_booking.game.match.match_start_datetime))
        else:
            game_start_time = convert_utc_into_ist(str(player_booking.game.match.match_start_datetime), 30)
        return {
            "game_id": player_booking.game.game_id,
            "match_name": player_booking.game.match.match_name,
            "match_type": player_booking.game.match.match_type,
            "game_start_time": str(game_start_time),
            "game_type": player_booking.game.game_type,
            "game_status": player_booking.game.game_status,
            "team_won": player_booking.game.team_won,
            "player_bid_price": str(player_booking.player_bid_price),
            "player_bid_team": player_booking.player_bid_team,
            "player_bid_multiplier": str(player_booking.player_bid_multiplier),
            "player_won_price": str(player_booking.player_won_price),
            "is_player_won": player_booking.is_player_won
        }


class RetrieveGamesByMatchService(object):
    """
    This class handles GET requests to the endpoint and returns the details of the games in a match
    GET /retrieve_game_by_match/{match_id}
    {
    "playerDetails": {
        "name": null,
        "email": "",
        "phone": "8709996580"
    },
    "games": [
        {
            "game_type": "WIN_PREDICT",
            "game_status": "COMPLETED",
            "first_team_bid_multiplier": "1.50",
            "second_team_bid_multiplier": "2.00",
            "match": 1,
            "game_id": 1
        },
        {
            "game_type": "TOSS_PREDICT",
            "game_status": "COMPLETED",
            "first_team_bid_multiplier": "1.80",
            "second_team_bid_multiplier": "1.70",
            "match": 1,
            "game_id": 2
        }
    ]
}
    """

    def __init__(self, logger):
        """
        Initializes the service with a logger.

        :param logger: Logger client used for logging.
        """
        self.logger = logger

    @validate_token
    def on_get(self, req, resp, **kwargs):
        """
        This method handles GET requests to the endpoint and returns the details of the games in a match
        """
        try:
            # Get the match_id from the request path
            match_id = kwargs.get("match_id")
            if match_id is None:
                # Raise an error if match_id is not provided
                raise ValueError("Missing match_id in request path")

            # Check if match with the provided id exists
            if Match.objects.filter(match_id=match_id).exists():
                match = Match.objects.get(match_id=match_id)
            else:
                # Raise an error if match with the provided id does not exist
                raise Match.DoesNotExist("Match with id {} does not exist".format(match_id))

            # All games in the match
            games_in_match = match.game_set.all()

            # Retrieve user details using token
            token = kwargs.get("token")
            player = Player.objects.filter(token__token_id=token).first()
            if not player:
                self.logger.error(f"MyGameService: Player with token {token} not found")
                resp.status = falcon.HTTP_400
                resp.text = json.dumps({"error": "Invalid token"})
                return

            # Prepare the response
            response = {"playerDetails": {"name": player.name, "email": player.email, "phone": player.phone},
                        "games": []}
            for game in games_in_match:
                response["games"].append(self.get_upcoming_resp(game))

            # Return a successful response
            resp.status = falcon.HTTP_202
            resp.text = json.dumps(response)
            self.logger.info(f"GET request to RetrieveGamesByMatchService endpoint successfully processed")
        except ValueError as e:
            # Handle missing match_id error
            resp.status = falcon.HTTP_400
            resp.text = json.dumps({"error": str(e)})
            self.logger.error(f"Error in GET request to RetrieveGamesByMatchService endpoint: {str(e)}")
        except Match.DoesNotExist as e:
            # Handle non-existent match error
            resp.status = falcon.HTTP_404
            resp.text = json.dumps({"error": str(e)})
            self.logger.error(f"Error in GET request to RetrieveGamesByMatchService endpoint: {str(e)}")
        except Exception as e:
            # Handle any other unexpected error
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": str(e)})
            self.logger.error(f"Error in GET request to RetrieveGamesByMatchService endpoint: {str(e)}")

    @staticmethod
    def get_upcoming_resp(game):
        if game.game_type == "WIN_PREDICT":
            game_start_time = convert_utc_into_ist(str(game.match.match_start_datetime))
        else:
            game_start_time = convert_utc_into_ist(str(game.match.match_start_datetime), 30)
        return {
            "game_id": game.game_id,
            "game_type": str(game.game_type),
            "game_status": str(game.game_status),
            "game_start_time": str(game_start_time),
            "first_team_bid_multiplier": str(game.first_team_bid_multiplier),
            "second_team_bid_multiplier": str(game.second_team_bid_multiplier),
            "match_name": str(game.match.match_name)
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

    matchService = MatchService(logger=logger)
    app.add_route('/matches', matchService)

    myGameService = MyGameService(logger=logger)
    app.add_route('/my_games', myGameService)

    # GET /retrieve_game_by_match/{match_id}
    retrieveGamesByMatch = RetrieveGamesByMatchService(logger=logger)
    app.add_route('/retrieve_games_by_match/{match_id}', retrieveGamesByMatch)

    healthCheck = HealthCheck()
    app.add_route('/healthcheck', healthCheck)

    logger.info("Cricbett-Feeds API is live now!")

    return app


# Load the configuration file
config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config/feeds_config.yaml")

# Open and read the configuration file into the config variable
with open(config_file, 'r') as cf:
    config = yaml.safe_load(cf)

# Setup LoggingClient by passing the config
logger_client = LoggerClient("cricbett-feeds", config)

# Initialize and start the service using the config
api = initialize_and_start_service(config, logger_client)
