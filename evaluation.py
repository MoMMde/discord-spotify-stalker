from dataclasses import dataclass
from pymongo import MongoClient
from .core import SpotifyStatistic

def open_database_connection(mongo_uri, mongo_database):
    client = MongoClient(mongo_uri)
    db = client.get_database(mongo_database)
    collection = db.get_collection("spotify_statistics")
    return db, collection

def get_all_songs(collection) -> list[SpotifyStatistic]:
    cursor = collection.find({})
    all_songs = []
    for document in cursor:
        all_songs.append(SpotifyStatistic(
            song=document['song'],
            spotify_id=document['spotify_id'],
            artist=document['artist'],
            album=document['album'],
            song_start=document['song_start'],
            song_probably_end=document['song_probably_end'],
            discord_id=document['discord_id'],
            discord_name=document['discord_name']
        ))
    return all_songs

def get_least_listened_songs(songs: list[SpotifyStatistic]) -> dict:
    if len(songs) == 0:
        return None
    times_in_list = {}
    for song in songs:
        times_in_list[song.spotify_id] = times_in_list.get(song.spotify_id, 0) + 1
    
    # Stolen from https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
    times_in_list = dict(sorted(times_in_list.items(), key=lambda item: item[1]))
    result = {}
    for song in times_in_list.keys():
        result[filter(lambda x: x.spotify_id == song, songs)[0]] = times_in_list[song]
    return result

def get_most_listened_songs(songs: list[SpotifyStatistic]) -> dict:
    return {v: k for k, v in get_least_listened_songs(songs).items()}

def find_all_songs_by_artist(songs: list[SpotifyStatistic], artist: str) -> list[SpotifyStatistic]:
    return list(filter(lambda x: x.artist == artist, songs))

def find_songs_listened_by_two_parties(songs: list[SpotifyStatistic], user_1: str, user_2: str) -> list[SpotifyStatistic]:
    return list(filter(lambda x: x.discord_id in [user_1, user_2], songs))

def find_songs_by_discord_id(songs: list[SpotifyStatistic], discord_id: str) -> list[SpotifyStatistic]:
    return list(filter(lambda x: x.discord_id == discord_id, songs))