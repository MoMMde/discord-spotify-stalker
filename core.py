from dataclasses import dataclass
from datetime import datetime
import json
import websocket
import os
import sys
import threading
import logging
import schedule
import argparse
import time
from pymongo import MongoClient


TOKEN = os.getenv('TOKEN')
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DATABASE = os.getenv('MONGO_DATABASE')

LOG = logging.getLogger("Spoticheck")

WEBSOCKET = "wss://gateway.discord.gg/?encoding=json"

DISCORD_HEADER = {
   'authorization': TOKEN
}

TARGET_USERS = os.getenv("TARGET_USERS").split(",")

AUTH_PAYLOAD = {
    "op": 2,
    "d": {
        "token": TOKEN,
        "intents": 512,
        "presence": {
            "activity": [],
            "afk": False,
            "status": "online",
            "since": 0,
        },
        "properties": {
            "$os": "linux",
            "$browser": "chrome",
            "$device": "pc"
        }
    }
}

current_listeners = []

@dataclass
class SpotifyStatistic():
    song: str
    spotify_id: str
    artist: str
    album: str
    song_start: int
    song_probably_end: int
    discord_id: str
    discord_name: str

def receive_json(ws):
    response = ws.recv()
    if response:
        return json.loads(response)

def listen_for_events(ws, collection):
    while 1:
        # Handles when the WS is closed and reports an error
        if not ws.connected:
            LOG.error("Websocket is DISCONNECTED")
            exit(1)
            return
        LOG.debug('Listening for events...')
        try:
            event = receive_json(ws)
            event_type = event['t']
            LOG.debug('Received: %s' % event_type)
            match event_type:
                case 'READY':
                    LOG.info("Ready")
                    pass
                case 'PRESENCE_UPDATE':
                    event = event['d']
                    user_id = event['user']['id']
                    user_name = event['user']['username']
                    #LOG.info("Presence update by %s" % user_name)
                    if not any([activity['name'] == 'Spotify' for activity in event['activities']]):
                        if user_id in current_listeners:
                            current_listeners.remove(user_id)
                            LOG.info("%s stopped listening" % user_name)
                        pass
                    activity = [activity for activity in event['activities'] if activity['name'] == 'Spotify'][0]
                    if user_id not in TARGET_USERS and TARGET_USERS != []:
                        pass
                    current_listeners.append(user_id)
                    statistics = SpotifyStatistic(
                        song=activity['details'], 
                        artist=activity['state'], 
                        album=activity['assets']['large_text'], 
                        song_start=activity['timestamps']['start'], 
                        song_probably_end=activity['timestamps']['end'], 
                        discord_id=user_id, 
                        spotify_id=activity['assets']['large_image'],
                        discord_name=user_name
                    )
                    LOG.info('{} is listening to {} by {} inside of the {} album'.format(statistics.discord_name, statistics.song, statistics.artist, statistics.album))
                    try:
                        collection.insert_one(statistics.__dict__)
                    except:
                        LOG.error("There was an exception on the database write task")
                        pass
                    pass
                case _:
                    pass
        except:
            pass

def open_websocket():
    ws = websocket.WebSocket()
    ws.connect(WEBSOCKET)
    heartbeat_interval = receive_json(ws)["d"]["heartbeat_interval"]
    ws.send(json.dumps(AUTH_PAYLOAD))
    return ws, heartbeat_interval

def send_heartbeat(ws):
    ws.send(json.dumps({
        "op": 1,
        "d": None
    }))
    LOG.info("Sent Heartbeat: %s" % datetime.now())

def send_heartbeat_thread(ws):
    schedule.every(heartbeat_interval / 1000).seconds.do(send_heartbeat, ws)
    while True:
        schedule.run_pending()
        time.sleep(1)

def handle_logging():
    formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    file_handler = logging.FileHandler('logs/' + str(datetime.now()) + ".log")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
        handlers=[
            file_handler,
            logging.StreamHandler(sys.stdout)
        ]    
    )

def get_arguments():
    parser = argparse.ArgumentParser(description='Spotify Checker')
    parser.add_argument('-t', '--token', help='Discord token (If not given in Environment, this is neccessary)', required=False, default=TOKEN)
    parser.add_argument('-d', '--debug', help='If the logger should print debug messages (will just send a lot of information)', required=False, default=False)
    parser.add_argument('-u', '--uri', help='URI to connect to Database (If not given in Environment, this is neccessary)', required=False, default=MONGO_URI)
    parser.add_argument('-b', '--database', help='Database for storage (If not given in Environment, this is neccessary)', required=False, default=MONGO_DATABASE)
    args = parser.parse_args()
    return args.token, args.debug, args.uri, args.database

def open_database_connection():
    client = MongoClient(MONGO_URI)
    db = client.get_database(MONGO_DATABASE)
    collection = db.get_collection("spotify_statistics")
    return db, collection

if __name__ == '__main__':    
    token, debug, uri, db = get_arguments()
    if token != None:
        TOKEN = token
    if uri != None:
        MONGO_URI = uri
    if db != None:
        MONGO_DATABASE = db
    if not MONGO_DATABASE:
        MONGO_DATABASE = 'spotify_checker'

    if not TOKEN or not MONGO_URI:
        LOG.error("Token or URI not given! Check Arguments or Environment Variables")
        exit(1)

    handle_logging()
    if debug:
        print("**Printing debug messages enabled**")
        LOG.setLevel(logging.DEBUG)

    mongo_database, collection = open_database_connection()
    LOG.info("Connected to MongoDB: %s" % MONGO_DATABASE)

    ws, heartbeat_interval = open_websocket()
    LOG.info("WebSocket connected: %s" % ws.connected)

    heartbeat = threading.Thread(name='Heartbeat', target=send_heartbeat_thread, args=(ws,))
    heartbeat.start() 
    LOG.info("Heartbeat started with Interval of %s" % heartbeat_interval)

    listener = threading.Thread(name='WS-con', target=listen_for_events, args=(ws, collection))
    listener.start()
    LOG.info("Listener started")

    listener.join()
    heartbeat.join()