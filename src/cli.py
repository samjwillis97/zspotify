"""
CLI Interface Handler
"""
from loguru import logger

import spotify_api
import helpers


def handle(api: spotify_api.Spotify, args: list) -> None:
    """ handles CLI input """
    if args[1] == "search":
        search_string(api, args)
    elif args[1] == "-p" or args[1] == "--playlist":
        playlist(api)
    elif args[1] == "-ls" or args[1] == "--liked-songs":
        liked_songs(api)
    elif args[1] == "-w" or args[1] == "--web":
        web_server(api)
    elif args[1] == "-h" or args[1] == "--help":
        help()
    else:
        unrecognized()


def playlist(api: spotify_api.Spotify):
    """ Downloads Users Playlists """
    api.download_from_user_playlist()


def liked_songs(api: spotify_api.Spotify):
    """ Download Users Liked Songs """
    for song in api.get_saved_tracks():
        if not song['track']['name']:
            print(
                "###   SKIPPING:  SONG DOES NOT EXISTS ON SPOTIFY ANYMORE   ###")
        else:
            api.download_track(song['track']['id'], "Liked Songs/")
        print("\n")


def web_server(api: spotify_api.Spotify):
    """ Runs a Web Server to Interact With """
    logger.info("Please Implement Me :(")


def search_string(api: spotify_api.Spotify, args: list):
    """ Searches Spotify with given term and Downloads """
    track_id, album_id, playlist_id, episode_id, show_id, artist_id = helpers.regex_input_for_urls(args[2])

    if track_id is not None:
        api.download_track(track_id)
    elif artist_id is not None:
        api.download_artist_albums(artist_id)
    elif album_id is not None:
        api.download_album(album_id)
    elif playlist_id is not None:
        playlist_songs = api.get_playlist_songs(playlist_id)
        name, _ = api.get_playlist_info(playlist_id)
        for song in playlist_songs:
            api.download_track(song['track']['id'],
                               helpers.sanitize_data(name) + "/")
            print("\n")
    elif episode_id is not None:
        api.download_episode(episode_id)
    elif show_id is not None:
        for episode in api.get_show_episodes(show_id):
            api.download_episode(episode)
    else:
        try:
            if len(args) > 3:
                if args[2] == "artist":
                    api.search_artists(args[3])
                else:
                    unrecognized()
            else:
                api.search(args[2])
        finally:
            return


def show_help():
    """ Displays Help """


def unrecognized():
    """ Displays Unkown Argument + Help """
    show_help()
