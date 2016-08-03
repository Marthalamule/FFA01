import urllib.parse
from uuid import uuid4
import requests
import requests.auth
from flask import Flask, abort, request

from FFA.settings.client_config import *


def base_http_headers():
    return {'User-Agent': USER_AGENT}


app = Flask(__name__)


@app.route('/')
def homepage():
    index_html = '<p>Welcome to Fweddit Fleet Analytics</p><a href="%s">CREST Login</a>'
    return index_html % make_oauth_url()


def make_oauth_url():
    state = str(uuid4())
    save_created_state(state)
    header_params = {'response_type': 'code',
                     'redirect_uri': CLIENT_CALLBACK_URI,
                     'client_id': CLIENT_ID,
                     'scope': SCOPE,
                     'state': state}
    encoded_header = urllib.parse.urlencode(header_params)
    url = 'https://login.eveonline.com/oauth/authorize?{0}'.format(encoded_header)
    return url


def save_created_state(state):
    pass


def is_valid_state(state):
    return True


@app.route('/ffa')
def fweddit_fleet_analytics():
    error = request.args.get('error', '')
    if error:
        return 'Error: {0}'.format(error)
    state = request.args.get('state', '')
    if not is_valid_state(state):
        abort(403)
    code = request.args.get('code')
    access_token = get_token(code)
    player_crest_info = get_username(access_token)
    player_location_info = get_player_location(access_token)
    player_fleet_info = get_fleet_info(access_token)
    player_fleet_members = get_fleet_members(access_token)
    print('PLAYER CREST INFO: {0}'.format(player_crest_info))
    print('PLAYER LOCATION INFO: {0}'.format(player_location_info))
    print('PLAYER FLEET INFO: {0}'.format(player_fleet_info))
    print('PLAYER FLEET MEMBERS: {0}'.format(player_fleet_members))
    return 'Welcome to Fweddit Fleet Analytics {0}.'.format(player_crest_info['CharacterName'])


def get_token(code):
    post_data = {'Authorization': 'Basic {0}'.format(CLIENT_AUTH),
                 'grant_type': 'authorization_code',
                 'code': code}
    headers = base_http_headers()
    headers.update({'Authorization': 'Basic {0}'.format(CLIENT_AUTH)})
    response = requests.post('https://login.eveonline.com/oauth/token',
                             headers=headers,
                             data=post_data)
    token_json = response.json()
    access_token = token_json['access_token']
    return access_token


def get_username(access_token):
    headers = base_http_headers()
    headers.update({'Authorization': 'Bearer {0}'.format(access_token)})
    response = requests.get('https://login.eveonline.com/oauth/verify', headers=headers)
    crest_json = response.json()
    return crest_json


def get_fleet_info(access_token):
    headers = base_http_headers()
    headers.update({'Authorization': 'Bearer {0}'.format(access_token)})
    crest_fleet_str = 'https://crest-tq.eveonline.com/fleets/1085911246391/'
    response = requests.get(crest_fleet_str, headers=headers)
    crest_fleet_response = response.json()
    return crest_fleet_response


def get_fleet_members(access_token):
    headers = base_http_headers()
    headers.update({'Authorization': 'Bearer {0}'.format(access_token)})
    player_fleet_info = get_fleet_info(access_token)
    fleet_members_url = player_fleet_info['members']['href']
    crest_fleet_members = requests.get(fleet_members_url, headers=headers)
    crest_fleet_members_response = crest_fleet_members.json()
    return crest_fleet_members_response


def get_player_location(access_token):
    headers = base_http_headers()
    headers.update({'Authorization': 'Bearer {0}'.format(access_token)})
    player_crest_info = get_username(access_token)
    player_character_id = player_crest_info['CharacterID']
    crest_loc_str = 'https://crest-tq.eveonline.com/characters/{0}/location/'.format(player_character_id)
    response = requests.get(crest_loc_str, headers=headers)
    crest_location_response = response.json()
    return crest_location_response

if __name__ is '__main__':
    app.run(debug=True, port=4270)
