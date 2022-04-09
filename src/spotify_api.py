"""
Spotify API
This file contains methods to interact with Spotify's API.

"""
import os
import re
import time
import json
import requests
from pprint import pprint

from tqdm import tqdm
from librespot.metadata import TrackId, EpisodeId
from librespot.audio.decoders import VorbisOnlyAudioQuality
from loguru import logger

import helpers
from auth import Client
import load_env as env

requests.adapters.DEFAULT_RETRIES = env.DEFAULT_RETRIES


class Spotify():
    """ Class to interace with Spotify API """
    _client: Client = None

    def __init__(self, client: Client):
        self._client = client

    # Podcast Methods

    # TODO: Name Outputs
    def get_episode_info(self, episode_id: str) -> (str, str):
        """ Get Podcast Episode Info  """
        info = json.loads(requests.get(
            "https://api.spotify.com/v1/episodes/" +
            episode_id, headers=
            {
                "Authorization": f"Bearer {self._client.user_read_email_token()}"
            }
        ).text)
        if "error" in info:
            return None, None
        return helpers.sanitize_data(info["show"]["name"]), helpers.sanitize_data(info["name"])

    # TODO: Test Output
    def get_show_episodes(self, show_id: str) -> list[str]:
        """ returns episodes of a show """
        episodes = []
        offset = 0
        limit = 50

        while True:
            headers = {'Authorization': f'Bearer {self._client.user_read_email_token()}'}
            params = {'limit': limit, 'offset': offset}
            resp = requests.get(
                f'https://api.spotify.com/v1/shows/{show_id}/episodes', headers=headers, params=params).json()
            offset += limit
            for episode in resp["items"]:
                episodes.append(episode["id"])

            if len(resp['items']) < limit:
                break
        return episodes

    def download_episode(self, episode_id: str) -> None:
        """ downloads episode """
        podcast_name, episode_name = self.get_episode_info(episode_id)
        extra_paths = podcast_name + "/"

        if podcast_name is None:
            print("###   SKIPPING: (EPISODE NOT FOUND)   ###")
        else:
            filename = podcast_name + " - " + episode_name
            episode_id = EpisodeId.from_base62(episode_id)
            stream = self._client.session().content_feeder().load(
                episode_id, VorbisOnlyAudioQuality(self._client.quality), False, None)
            os.makedirs(env.ROOT_PODCAST_PATH + extra_paths, exist_ok=True)

            total_size = stream.input_stream.size
            with open(
                    env.ROOT_PODCAST_PATH +
                    extra_paths +
                    filename + ".wav", 'wb') as file, tqdm(
                desc=filename,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024
            ) as iterable:
                for _ in range(int(total_size / env.CHUNK_SIZE) + 1):
                    iterable.update(file.write(
                        stream.input_stream.stream().read(env.CHUNK_SIZE)))

    # Song Methods

    # TODO: Output Typing
    def get_song_info(self, song_id: str):
        """ Retrieves metadata for downloaded songs """
        try:
            info = json.loads(
                requests.get(
                    "https://api.spotify.com/v1/tracks?ids=" +
                    song_id +
                    '&market=from_token',
                    headers={
                        "Authorization": f"Bearer {self._client.user_read_email_token()}"
                    }).text)['tracks'][0]

            artists = []
            for data in info['artists']:
                artists.append(helpers.sanitize_data(data['name']))
            album_name = helpers.sanitize_data(info["name"])
            name = helpers.sanitize_data(info['name'])
            image_url = info['album']['images'][0]['url']
            release_year = info['album']['release_date'].split("-")[0]
            disc_number = info['disc_number']
            track_number = info['track_number']
            scraped_song_id = info['id']
            is_playable = info['is_playable']

            return (
                artists,
                album_name,
                name,
                image_url,
                release_year,
                disc_number,
                track_number,
                scraped_song_id,
                is_playable)
        except Exception as error:
            print("###   get_song_info - FAILED TO QUERY METADATA   ###")
            print(error)
            print(song_id)
            return None

    # TODO: Convert to Dict?
    def download_track(
            self,
            track_id: str,
            output_dir="",
            prefix=False,
            prefix_value='',
    ) -> None:
        """ Downloads raw song audio from Spotify """
        try:
            # TODO: ADD disc_number IF > 1 
            artists, album_name, name, image_url, release_year, disc_number, track_number, scraped_song_id, is_playable = self.get_song_info(
                track_id)

            _artist = artists[0]
            if prefix:
                _track_number = str(track_number).zfill(2)
                song_name = f'{_artist} - {album_name} - {_track_number}. {name}.{env.MUSIC_FORMAT}'
                filename = os.path.join(env.ROOT_PATH, output_dir, song_name)
            else:
                song_name = f'{_artist} - {album_name} - {name}.{env.MUSIC_FORMAT}'
                filename = os.path.join(env.ROOT_PATH, output_dir, song_name)
        except Exception as error:
            print("###   SKIPPING SONG - FAILED TO QUERY METADATA   ###")
            print(
                f" download_track FAILED: [{track_id}][{output_dir}][{prefix}][{prefix_value}]")
            print("SKIPPING SONG: ", error)
            time.sleep(60)
            # TODO: Check if this is correct
            self.download_track(track_id, output_dir, prefix=prefix, prefix_value=prefix_value)
        else:
            try:
                if not is_playable:
                    print("###   SKIPPING:", song_name, "(SONG IS UNAVAILABLE)   ###")
                else:
                    if os.path.isfile(filename) and os.path.getsize(filename) and env.SKIP_EXISTING_FILES:
                        print("###   SKIPPING: (SONG ALREADY EXISTS) :", song_name, "   ###")
                    else:
                        if track_id != scraped_song_id:
                            track_id = scraped_song_id

                        stream = self._client.session().content_feeder().load(
                            TrackId.from_base62(track_id),
                            VorbisOnlyAudioQuality(self._client.quality),
                            False,
                            None
                        )
                        os.makedirs(os.path.join(env.ROOT_PATH, output_dir), exist_ok=True)
                        total_size = stream.input_stream.size

                        with open(filename, 'wb') as file:
                            for _ in range(int(total_size / env.CHUNK_SIZE) + 1):
                                file.write(stream.input_stream.stream().read(env.CHUNK_SIZE))

                        if not env.RAW_AUDIO_AS_IS:
                            helpers.convert_audio_format(filename, self._client.quality)
                            helpers.set_audio_tags(filename, artists, name, album_name,
                                                   release_year, disc_number, track_number, track_id)
                            helpers.set_music_thumbnail(filename, image_url)

                        if not env.OVERRIDE_AUTO_WAIT:
                            # TODO: Add in Random here
                            time.sleep(env.ANTI_BAN_WAIT_TIME)
            except Exception as e:
                print(e)
                print("###   SKIPPING:", song_name, "(GENERAL DOWNLOAD ERROR)   ###")
                if os.path.exists(filename):
                    os.remove(filename)
                print(
                    f" download_track GENERAL DOWNLOAD ERROR: [{track_id}][{output_dir}][{prefix}][{prefix_value}]")
                self.download_track(
                    track_id,
                    output_dir,
                    prefix=prefix,
                    prefix_value=prefix_value
                )

    # Album Methods
    def get_album_name(self, album_id: str) -> (str, str, str, str):
        """ Returns album name """
        headers = {'Authorization': f'Bearer {self._client.user_read_email_token()}'}
        response = requests.get(
            f'https://api.spotify.com/v1/albums/{album_id}', headers=headers).json()

        if match := re.search(r'(\d{4})', response['release_date']):
            return (
                response['artists'][0]['name'],
                match.group(1),
                helpers.sanitize_data(response['name']),
                response['total_tracks'])
        return (
            response['artists'][0]['name'],
            response['release_date'],
            helpers.sanitize_data(response['name']),
            response['total_tracks'])

    def get_artist_albums(self, artist_id: str) -> list[str]:
        """ Returns artist's albums """
        headers = {'Authorization': f'Bearer {self._client.user_read_email_token()}'}
        resp = requests.get(
            f'https://api.spotify.com/v1/artists/{artist_id}/albums', headers=headers).json()
        # Return a list each album's id
        return [resp['items'][i]['id'] for i in range(len(resp['items']))]

    def get_album_tracks(self, album_id: str) -> list[str]:
        """ Returns album tracklist """
        songs = []
        offset = 0
        limit = 50
        include_groups = 'album,compilation'

        while True:
            headers = {'Authorization': f'Bearer {self._client.user_read_email_token()}'}
            params = {'limit': limit, 'include_groups': include_groups, 'offset': offset}
            resp = requests.get(
                f'https://api.spotify.com/v1/albums/{album_id}/tracks', headers=headers, params=params).json()
            offset += limit
            songs.extend(resp['items'])

            if len(resp['items']) < limit:
                break

        return songs

    def download_album(self, album_id: str) -> None:
        """ Downloads songs from an album """
        disc_number_flag = False
        artist, album_release_date, album_name, total_tracks = self.get_album_name(album_id)
        tracks = self.get_album_tracks(album_id)

        print(f"\n  {artist} - ({album_release_date}) {album_name} [{total_tracks}]")

        for track in tracks:
            if track['disc_number'] > 1:
                disc_number_flag = True
        if disc_number_flag:
            for n, track in tqdm(enumerate(tracks, start=1), unit_scale=True, unit='Song', total=len(tracks)):
                disc_number = str(track['disc_number']).zfill(2)
                self.download_track(
                    track['id'],
                    os.path.join(f"{artist}", f"{album_name}", f"CD {disc_number}"),
                    prefix=True,
                    prefix_value=str(n)
                )
        else:
            for n, track in tqdm(enumerate(tracks, start=1), unit_scale=True, unit='Song', total=len(tracks)):
                self.download_track(
                    track['id'],
                    os.path.join(f"{artist}", f"{album_name}"),
                    prefix=True,
                    prefix_value=str(n)
                )

    def download_artist_albums(self, artist_id: str) -> None:
        """ Downloads albums of an artist """
        albums = self.get_artist_albums(artist_id)
        for album_id in albums:
            self.download_album(album_id)

    # Playlist Methods

    def get_playlist_songs(self, playlist_id: str) -> list[str]:
        """ returns list of songs in a playlist """
        songs = []
        offset = 0
        limit = 100
        while True:
            headers = {'Authorization': f'Bearer {self._client.user_read_email_token()}'}
            params = {'limit': limit, 'offset': offset}
            resp = requests.get(
                f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers=headers, params=params).json()
            offset += limit
            songs.extend(resp['items'])

            if len(resp['items']) < limit:
                break
        return songs

    def get_playlist_info(self, playlist_id: str) -> (str, str):
        """ Returns information scraped from playlist """
        headers = {'Authorization': f'Bearer {self._client.user_read_email_token()}'}
        resp = requests.get(
            f'https://api.spotify.com/v1/playlists/{playlist_id}?fields=name,owner(display_name)&market=from_token',
            headers=headers).json()
        return resp['name'].strip(), resp['owner']['display_name'].strip()

    # TODO: This could do with some refactoring..
    def download_playlist(self, playlists, playlist_choice):
        """Downloads all the songs from a playlist"""
        playlist_songs = self.get_playlist_songs(
            playlists[int(playlist_choice) - 1]['id'])

        for song in playlist_songs:
            if song['track']['id'] is not None:
                self.download_track(song['track']['id'], helpers.sanitize_data(
                    playlists[int(playlist_choice) - 1]['name'].strip()) + "/")
            print("\n")

    # User Methods

    def get_user_playlists(self) -> list[str]:
        """ Returns list of users playlists """
        playlists = []
        limit = 50
        offset = 0
        while True:
            headers = {'Authorization': f'Bearer {self._client.user_read_email_token()}'}
            params = {'limit': limit, 'offset': offset}
            resp = requests.get("https://api.spotify.com/v1/me/playlists",
                                headers=headers, params=params).json()
            offset += limit
            playlists.extend(resp['items'])

            if len(resp['items']) < limit:
                break
        return playlists

    def download_from_user_playlist(self):
        """ Select which playlist(s) to download """
        playlists = self.get_user_playlists()

        count = 1
        for playlist in playlists:
            print(str(count) + ": " + playlist['name'].strip())
            count += 1

        print("\n> SELECT A PLAYLIST BY ID")
        print("> SELECT A RANGE BY ADDING A DASH BETWEEN BOTH ID's")
        print("> For example, typing 10 to get one playlist or 10-20 to get\nevery playlist from 10-20 (inclusive)\n")

        playlist_choices = input("ID(s): ").split("-")

        if len(playlist_choices) == 1:
            self.download_playlist(playlists, playlist_choices[0])
        else:
            start = int(playlist_choices[0])
            end = int(playlist_choices[1]) + 1

            print(f"Downloading from {start} to {end}...")

            for playlist in range(start, end):
                self.download_playlist(playlists, playlist)

            print("\n**All playlists have been downloaded**\n")

    def get_saved_tracks(self) -> list[str]:
        """ Returns user's saved tracks """
        songs = []
        offset = 0
        limit = 50

        logger.debug(self._client.session().tokens().get_token())

        while True:
            headers = {'Authorization': f'Bearer {self._client.user_read_email_token()}'}
            params = {'limit': limit, 'offset': offset}
            resp = requests.get('https://api.spotify.com/v1/me/tracks',
                                headers=headers, params=params).json()
            logger.debug(resp)
            # TODO: 403 Insufficient Client Scope... On test user
            offset += limit
            songs.extend(resp['items'])

            if len(resp['items']) < limit:
                break
        return songs

    def _search_by_type(self, search: str, types: list[str]) -> dict:
        """ Searches Spotify's API for artists """
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            {
                "limit": env.LIMIT,
                "offset": "0",
                "q": search,
                "type": str(",".join(map(str, types))),
            },
            headers={"Authorization": f"Bearer {self._client.user_read_email_token()}"},
        )

        items = {}
        for type_str in types:
            # TODO: This is the dodgiest fix possible
            items[type_str] = resp.json()[type_str + "s"]["items"]

        return items

    def search_artists(self, search: str) -> list[dict]:
        artists = self._search_by_type(search, ["artist"])["artist"]
        helpers.print_artist_list(artists)
        return artists

    def search(self, search_term: str):
        """ Searches Spotify's API for relevant data """
        # TODO: Investigate breaking this up a bit..

        # Does a Generic Search
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            {
                "limit": env.LIMIT,
                "offset": "0",
                "q": search_term,
                "type": "track,album,playlist,artist"
            },
            headers={"Authorization": f"Bearer {self._client.user_read_email_token()}"},
        )

        # Gets Tracks from Search
        i = 1
        tracks = resp.json()["tracks"]["items"]
        if len(tracks) > 0:
            print("###  TRACKS  ###")
            for track in tracks:
                if track["explicit"]:
                    explicit = "[E]"
                else:
                    explicit = ""
                print(f"{i}, {track['name']} {explicit} | {','.join([artist['name'] for artist in track['artists']])}")
                i += 1
            total_tracks = i - 1
            print("\n")
        else:
            total_tracks = 0

        albums = resp.json()["albums"]["items"]
        if len(albums) > 0:
            print("###  ALBUMS  ###")
            for album in albums:
                # print("==>",album,"\n")
                _year = re.search('(\d{4})', album['release_date']).group(1)
                print(
                    f"{i}, ({_year}) {album['name']} [{album['total_tracks']}] | {','.join([artist['name'] for artist in album['artists']])}")
                i += 1
            total_albums = i - total_tracks - 1
            print("\n")
        else:
            total_albums = 0

        playlists = resp.json()["playlists"]["items"]
        total_playlists = 0
        print("###  PLAYLISTS  ###")
        for playlist in playlists:
            print(f"{i}, {playlist['name']} | {playlist['owner']['display_name']}")
            i += 1
        total_playlists = i - total_albums - total_tracks - 1
        print("\n")

        artists = resp.json()["artists"]["items"]
        helpers.print_artist_list(artists, i)
        total_artists = len(artists)
        i += total_artists

        if len(tracks) + len(albums) + len(playlists) == 0:
            print("NO RESULTS FOUND - EXITING...")
        else:

            selection = str(input("SELECT ITEM(S) BY ID: "))
            inputs = helpers.split_input(selection)

            if not selection:
                return

            for pos in inputs:
                position = int(pos)
                if position <= total_tracks:
                    track_id = tracks[position - 1]["id"]
                    self.download_track(track_id)
                elif position <= total_albums + total_tracks:
                    # print("==>" , position , " total_albums + total_tracks ", total_albums + total_tracks )
                    self.download_album(albums[position - total_tracks - 1]["id"])
                elif position <= total_albums + total_tracks + total_playlists:
                    # print("==> position: ", position ," total_albums + total_tracks + total_playlists ", total_albums + total_tracks + total_playlists )
                    playlist_choice = playlists[position -
                                                total_tracks - total_albums - 1]
                    playlist_songs = self.get_playlist_songs(playlist_choice['id'])
                    for song in playlist_songs:
                        if song['track']['id'] is not None:
                            self.download_track(song['track']['id'], helpers.sanitize_data(
                                playlist_choice['name'].strip()) + "/")
                            print("\n")
                else:
                    # 5eyTLELpc4Coe8oRTHkU3F
                    # print("==> position: ", position ," total_albums + total_tracks + total_playlists: ", position - total_albums - total_tracks - total_playlists )
                    artists_choice = artists[position - total_albums - total_tracks - total_playlists - 1]
                    albums = self.get_artist_albums(artists_choice['id'])
                    i = 0

                    print("\n")
                    print("ALL ALBUMS: ", len(albums), " IN:", str(set(album['album_type'] for album in albums)))

                    for album in albums:
                        if artists_choice['id'] == album['artists'][0]['id'] and album['album_type'] != 'single':
                            i += 1
                            year = re.search('(\d{4})', album['release_date']).group(1)
                            print(
                                f" {i} {album['artists'][0]['name']} - ({year}) {album['name']} [{album['total_tracks']}] [{album['album_type']}]")
                    total_albums_downloads = i
                    print("\n")

                    # print('\n'.join([f"{album['name']} - [{album['album_type']}] | {'/'.join([artist['name'] for artist in album['artists']])} " for album in sorted(albums, key=lambda k: k['album_type'], reverse=True)]))

                    for i in range(8)[::-1]:
                        print("\rWait for Download in %d second(s)..." % (i + 1), end="")
                        time.sleep(1)

                    print("\n")
                    i = 0
                    for album in albums:
                        if artists_choice['id'] == album['artists'][0]['id'] and album['album_type'] != 'single':
                            i += 1
                            year = re.search('(\d{4})', album['release_date']).group(1)
                            print(
                                f"\n\n\n{i}/{total_albums_downloads} {album['artists'][0]['name']} - ({year}) {album['name']} [{album['total_tracks']}]")
                            self.download_album(album['id'])
                            for i in range(env.ANTI_BAN_WAIT_TIME_ALBUMS)[::-1]:
                                print("\rWait for Next Download in %d second(s)..." % (i + 1), end="")
                                time.sleep(1)
