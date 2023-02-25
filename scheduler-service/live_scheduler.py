import json
import os
import sys
import traceback

import falcon
import requests
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.wsgi import get_wsgi_application

from clients.logger_client import LoggerClient

sys.path.append(os.pardir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'cricbett_db.settings'
get_wsgi_application()

from db.models import Game


def get_game_state(match_search_id):
    try:
        match_status_url = 'https://www.cricbuzz.com/api/cricket-match/commentary/{}'.format(str(match_search_id))
        response = requests.get(match_status_url)
        game_state = ""
        if response.status_code == 200:
            data = response.json()
            # Fetch game state
            game_state = data['matchHeader']['state']
        return game_state
    except Exception:
        return ""


def get_game_results_status(match_search_id):
    try:
        match_status_url = 'https://www.cricbuzz.com/api/cricket-match/commentary/{}'.format(str(match_search_id))
        response = requests.get(match_status_url)
        team_toss_won, team_match_won = "", ""
        if response.status_code == 200:
            data = response.json()
            # Fetch Toss Details
            team_toss_won = data['matchHeader']['tossResults']['tossWinnerName']
            # Fetch Game Details
            team_match_won = data['matchHeader']['result']['winningTeam']
        return team_toss_won, team_match_won
    except Exception as e:
        return "", ""


def settle_player_wallet(game_id):
    """
    Handles GET requests to the endpoint.
    """
    try:
        if game_id is None:
            # Raise an error if game_id is not provided
            print("Missing game_id in request path")
            raise ValueError("Missing game_id in request path")

        # Check if game with the provided id exists
        if Game.objects.filter(game_id=game_id).exists():
            game = Game.objects.get(game_id=game_id)
        else:
            # Raise an error if game with the provided id does not exist
            print(f"Game with id {game_id} does not exist")
            raise Game.DoesNotExist("Game with id {} does not exist".format(game_id))

        # Check if game_status is not completed
        if game.game_status != 'COMPLETED':
            print(f"Game:{game_id} is still {game.game_status}")
            raise ValueError(f"Game:{game_id} is still {game.game_status}")

        # Get the team that won the game
        team_won = game.team_won

        # Get all bookings for the game
        bookings = game.booking_set.all()

        # Iterate through all bookings in the game
        for booking in bookings:
            player_bid_team = booking.player_bid_team
            # Check if Booking is not already processed
            if booking.is_player_won is True or booking.is_player_won is False:
                print(f"Booking:{booking.booking_id} is already processed.")
                continue
            if player_bid_team == team_won:
                # Prediction is correct
                booking.is_player_won = True
                # Add winning amount to player's wallet
                add_amount_to_player_wallet(booking)
            else:
                # Prediction is incorrect
                booking.is_player_won = False
            booking.save()

        # Log a success message
        print(f"Successfully settled payment for game_id: {game_id}")

    except ValueError as e:
        # Handle missing game_id error
        print(f"Error in GET request: {traceback.format_exc()}")
    except Game.DoesNotExist as e:
        # Handle non-existent game error
        print(f"Error in GET request to LoadWalletEndpoint endpoint: {traceback.print_exc()}")
    except Exception as e:
        # Handle any other unexpected error
        print(f"Error in GET request to LoadWalletEndpoint endpoint: {traceback.print_exc()}")


def add_amount_to_player_wallet(booking):
    winning_amount = booking.player_won_price
    player_wallet = booking.player.wallet
    current_wallet_amount = player_wallet.wallet_amount
    player_wallet.wallet_amount = current_wallet_amount + winning_amount
    player_wallet.save()


def run_on_schedule():
    games = Game.objects.filter(game_status__in=['UPCOMING', 'LIVE'])
    for game in games:
        game_id = game.game_id
        match_search_id = game.match.match_search_id
        game_status = game.game_status  # Initially: UPCOMING

        # game_type is WIN_PREDICT
        if game.game_type == "WIN_PREDICT":
            buzz_game_state = get_game_state(match_search_id).lower()

            if buzz_game_state == 'in progress':
                match = game.match
                if match.match_status != 'LIVE':
                    match.match_status = 'LIVE'
                    match.save()
                # Game is UPCOMING
                if game_status != 'LIVE':
                    game.game_status = 'LIVE'
                    game.save()

            if game.game_status == 'LIVE':
                _, team_match_won = get_game_results_status(match_search_id=match_search_id)
                if team_match_won != '':
                    team_match_won = team_match_won.upper()
                    # WIN_PREDICT game is completed. Change game status to COMPLETED
                    teams = [game.match.first_team, game.match.second_team]
                    if team_match_won not in teams:
                        print(f"Invalid team_won value in request. Must be one from {str(teams)}")
                        return
                    game.game_status = 'COMPLETED'
                    game.team_won = team_match_won
                    game.save()
                    match = game.match
                    match.match_status = 'COMPLETED'
                    match.save()
                    settle_player_wallet(game_id)

        # game_type is TOSS_PREDICT
        else:
            team_toss_won, _ = get_game_results_status(match_search_id=match_search_id)
            if team_toss_won != '':
                team_toss_won = team_toss_won.upper()
                # TOSS_PREDICT game is completed. Change game status to COMPLETED
                teams = [game.match.first_team, game.match.second_team]
                if team_toss_won not in teams:
                    print(f"Invalid team_won value in request. Must be one from {str(teams)}")
                    return

                game.game_status = 'COMPLETED'
                game.team_won = team_toss_won
                game.save()
                match = game.match
                match.match_status = 'TOSS_DONE'
                match.save()
                settle_player_wallet(game_id)


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

    healthCheck = HealthCheck()
    app.add_route('/healthcheck', healthCheck)

    logger.info("Live Schedular Service is active now!")

    return app


# Load the configuration file
config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config/live_scheduler_config.yaml")

# Open and read the configuration file into the config variable
with open(config_file, 'r') as cf:
    config = yaml.safe_load(cf)

# Setup LoggingClient by passing the config
logger_client = LoggerClient("live-scheduler", config)

# Initialize and start the service using the config
api = initialize_and_start_service(config, logger_client)

sched = BackgroundScheduler(daemon=True)
sched.add_job(run_on_schedule, 'interval', seconds=5)
sched.start()
