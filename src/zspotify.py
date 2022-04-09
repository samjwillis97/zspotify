#! /usr/bin/env python3

"""
ZSpotify
It's like youtube-dl, but for Spotify.
"""

import json
import os
import os.path
import re
import sys
import time

import music_tag
import requests
from librespot.audio.decoders import AudioQuality, VorbisOnlyAudioQuality
from librespot.core import Session
from tqdm import tqdm
from loguru import logger

import load_env as env
import helpers
import auth
import spotify_api

requests.adapters.DEFAULT_RETRIES = env.DEFAULT_RETRIES


def main():
    # Pretty Printout
    helpers.splash()
    
    # Login to Spotify and get the Client
    client = auth.Client()
    spotify = spotify_api.Spotify(client)

    # Command Line Argument Given
    if len(sys.argv) > 1:
        if sys.argv[1] == "-p" or sys.argv[1] == "--playlist":
            spotify.download_from_user_playlist()
        elif sys.argv[1] == "-ls" or sys.argv[1] == "--liked-songs":
            for song in spotify.get_saved_tracks():
                if not song['track']['name']:
                    print(
                        "###   SKIPPING:  SONG DOES NOT EXISTS ON SPOTIFY ANYMORE   ###")
                else:
                    spotify.download_track(song['track']['id'], "Liked Songs/")
                print("\n")
        elif sys.argv[1] == "-w" or sys.argv[1] == "--web":
            logger.info("Launching Webserver")
        else:
            track_id_str, album_id_str, playlist_id_str, episode_id_str, show_id_str, artist_id_str = helpers.regex_input_for_urls(sys.argv[1])

            if track_id_str is not None:
                spotify.download_track(track_id_str)
            elif artist_id_str is not None:
                spotify.download_artist_albums(artist_id_str)
            elif album_id_str is not None:
                spotify.download_album(album_id_str)
            elif playlist_id_str is not None:
                playlist_songs = spotify.get_playlist_songs(playlist_id_str)
                name, creator = spotify.get_playlist_info(playlist_id_str)
                for song in playlist_songs:
                    spotify.download_track(song['track']['id'],
                                   helpers.sanitize_data(name) + "/")
                    print("\n")
            elif episode_id_str is not None:
                spotify.download_episode(episode_id_str)
            elif show_id_str is not None:
                for episode in spotify.get_show_episodes(show_id_str):
                    spotify.download_episode(episode)
    else:
        search_text = input("Enter search or URL: ")

        track_id_str, album_id_str, playlist_id_str, episode_id_str, show_id_str, artist_id_str = helpers.regex_input_for_urls(
            search_text)

        if track_id_str is not None:
            spotify.download_track(track_id_str)
        elif artist_id_str is not None:
            spotify.download_artist_albums(artist_id_str)
        elif album_id_str is not None:
            spotify.download_album(album_id_str)
        elif playlist_id_str is not None:
            playlist_songs = spotify.get_playlist_songs(playlist_id_str)
            name, creator = spotify.get_playlist_info(playlist_id_str)
            for song in playlist_songs:
                spotify.download_track(song['track']['id'],
                               helpers.sanitize_data(name) + "/")
                print("\n")
        elif episode_id_str is not None:
            spotify.download_episode(episode_id_str)
        elif show_id_str is not None:
            for episode in spotify.get_show_episodes(show_id_str):
                spotify.download_episode(episode)
        else:
            try:
                spotify.search(search_text)
            except:
                main()
            main()

if __name__ == "__main__":
    """ Main function """
    main()
