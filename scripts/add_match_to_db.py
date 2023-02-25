import os
import sys
from datetime import datetime
import re
import pytz
import requests
from bs4 import BeautifulSoup
from django.core.wsgi import get_wsgi_application


sys.path.append(os.pardir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'cricbett_db.settings'
get_wsgi_application()

from db.models import Match, Game


def add_match_to_db():
    try:
        url = "https://www.cricbuzz.com/cricket-schedule/upcoming-series/league"
        upcoming_matches = get_upcoming_cricket_match(url)
        for match_dict in upcoming_matches:
            match = create_cricket_match(match_dict)
            create_games_inside_match(match)

        print("matches added successfully")

    except KeyError as e:
        print(f"Missing required field in request body: {e}")
        return
    except Exception as e:
        print(f"Error: {e}")
        return


def create_cricket_match(match_dict):
    match = Match.objects.create(
        match_search_id=str(match_dict['match_search_id']),
        match_name=match_dict['match'],
        match_status='UPCOMING',
        match_start_datetime=match_dict['start_datetime'],
        match_venue=f"{match_dict['stadium']} {match_dict['city']}",
        match_type='CRICKET',
        first_team=match_dict['first_team'],
        second_team=match_dict['second_team']
    )
    return match


def create_games_inside_match(match):
    game_types = ['WIN_PREDICT', 'TOSS_PREDICT']
    for game_type in game_types:
        create_game_object(game_type, match)


def create_game_object(game_type, match):
    game = Game.objects.create(
        game_type=game_type,
        game_status='UPCOMING',
        # TODO: Write algo to dynamically generate team_bid_multiplier
        first_team_bid_multiplier=1.7,
        second_team_bid_multiplier=2.0,
        match=match
    )
    return game


def construct_match_id_list(match_id_tags):
    res = []
    for match_url in match_id_tags:
        a_tag = str(match_url.find('a')['href'])
        pattern = r"/(\d+)/"
        match_id = re.search(pattern, a_tag)
        if match_id:
            res.append(match_id.group(1))
    return res


def get_upcoming_cricket_match(url):
    upcoming_cricket_match = []
    total_teams_map = {}
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    # s = soup.find_all('div', {'id': 'international-list'})[0]
    tours = soup.find_all('a', class_='cb-mtchs-dy')
    timestamps = soup.find_all('span', class_='schedule-date')
    cities = soup.find_all('span', itemprop='addressLocality')
    stadium_name = soup.find_all('span', itemprop='name')
    match_id_tags = soup.find_all('div', itemtype="http://schema.org/SportsEvent")
    match_id_list = construct_match_id_list(match_id_tags)
    matches = []
    stadiums = []
    i = 0
    for item in stadium_name:
        if i % 2 == 0:
            matches.append(item['content'])
        else:
            stadiums.append(item.text)
        i = i + 1
    for match_id, tour, match, city, stadium, timestamp in zip(match_id_list, tours, matches, cities, stadiums,
                                                               timestamps):
        teams = match.split(",")[0].split(' vs ')
        first_team = str(teams[0]).strip().upper()
        second_team = str(teams[1]).strip().upper()
        total_teams_map[first_team] = total_teams_map.get(first_team, 1) + 1
        total_teams_map[second_team] = total_teams_map.get(second_team, 1) + 1
        # Checks to skip test matches
        if "test" in match.lower() or "day" in match.lower():
            continue
        data = {
            "match_search_id": match_id,
            "tour": tour.text,
            "match": match,
            "first_team": first_team,
            "second_team": second_team,
            "city": city.text,
            "stadium": stadium,
            "start_timestamp": timestamp['timestamp']
        }
        upcoming_cricket_match.append(data)

    IST = pytz.timezone('Asia/Kolkata')
    for d in upcoming_cricket_match:
        d['start_datetime'] = datetime.fromtimestamp(int(d['start_timestamp']) / 1000, tz=pytz.utc).astimezone(IST)

    sorted_data = sorted(upcoming_cricket_match, key=lambda x: x['start_timestamp'])
    return sorted_data

if __name__ == "__main__":
    add_match_to_db()