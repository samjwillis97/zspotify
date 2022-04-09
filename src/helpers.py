import os
import re
import time
import platform
import requests

import music_tag
from pydub import AudioSegment
from librespot.audio.decoders import AudioQuality

import load_env as env

requests.adapters.DEFAULT_RETRIES = env.DEFAULT_RETRIES

def splash():
    """ Displays splash screen """
    print("""
███████ ███████ ██████   ██████  ████████ ██ ███████ ██    ██
   ███  ██      ██   ██ ██    ██    ██    ██ ██       ██  ██
  ███   ███████ ██████  ██    ██    ██    ██ █████     ████
 ███         ██ ██      ██    ██    ██    ██ ██         ██
███████ ███████ ██       ██████     ██    ██ ██         ██
    """)


def clear_console():
    """ Clear the console window """
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def wait(seconds: int = 3):
    """ Pause for a set number of seconds """
    for i in range(seconds)[::-1]:
        print(f"\rWait for {i + 1} second(s)...")
        time.sleep(1)


def sanitize_data(value):
    """ Returns given string with problematic removed """
    sanitize = ["\\", "/", ":", "*", "?", "'", "<", ">", '"']
    for i in sanitize:
        value = value.replace(i, "")
    return value.replace("|", "-")


def split_input(selection):
    """ Returns a list of inputted strings """
    if "-" in selection:
        return list(range(int(selection.split('-')[0]), int(selection.split('-')[1] + 1)))
    return list(selection.strip().split(' '))


def convert_audio_format(filename, quality):
    """ Converts raw audio into playable mp3 or ogg vorbis """
    """ quality is the audio quality output"""
    #print("###   CONVERTING TO " + MUSIC_FORMAT.upper() + "   ###")
    raw_audio = AudioSegment.from_file(filename, format="ogg",
                                       frame_rate=44100, channels=2, sample_width=2)
    if quality == AudioQuality.VERY_HIGH:
        bitrate = "320k"
    else:
        bitrate = "160k"
    raw_audio.export(filename, format=env.MUSIC_FORMAT, bitrate=bitrate)

def convert_artist_format(artists):
    """ Returns converted artist format """
    formatted = ""
    for artist in artists:
        formatted += artist + ", "
    return formatted[:-2]


# TODO: Change to Dict
def set_audio_tags(filename, artists, name, album_name, release_year, disc_number, track_number, track_id_str):
    """ sets music_tag metadata """
    #print("###   SETTING MUSIC TAGS   ###")
    tags = music_tag.load_file(filename)
    tags['artist'] = convert_artist_format(artists)
    tags['tracktitle'] = name
    tags['album'] = album_name
    tags['year'] = release_year
    tags['discnumber'] = disc_number
    tags['tracknumber'] = track_number
    tags['comment'] = 'id[spotify.com:track'+track_id_str+']'
    tags.save()


def set_music_thumbnail(filename, image_url):
    """ Downloads cover artwork """
    #print("###   SETTING THUMBNAIL   ###")
    img = requests.get(image_url).content
    tags = music_tag.load_file(filename)
    tags['artwork'] = img
    tags.save()


def regex_input_for_urls(search_input):
    """ What the fuck does this do? """
    track_uri_search = re.search(
        r"^spotify:track:(?P<TrackID>[0-9a-zA-Z]{22})$", search_input)
    track_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/track/(?P<TrackID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    album_uri_search = re.search(
        r"^spotify:album:(?P<AlbumID>[0-9a-zA-Z]{22})$", search_input)
    album_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/album/(?P<AlbumID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    playlist_uri_search = re.search(
        r"^spotify:playlist:(?P<PlaylistID>[0-9a-zA-Z]{22})$", search_input)
    playlist_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/playlist/(?P<PlaylistID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    episode_uri_search = re.search(
        r"^spotify:episode:(?P<EpisodeID>[0-9a-zA-Z]{22})$", search_input)
    episode_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/episode/(?P<EpisodeID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    show_uri_search = re.search(
        r"^spotify:show:(?P<ShowID>[0-9a-zA-Z]{22})$", search_input)
    show_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/show/(?P<ShowID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    artist_uri_search = re.search(
        r"^spotify:artist:(?P<ArtistID>[0-9a-zA-Z]{22})$", search_input)
    artist_url_search = re.search(
        r"^(https?://)?open\.spotify\.com/artist/(?P<ArtistID>[0-9a-zA-Z]{22})(\?si=.+?)?$",
        search_input,
    )

    if track_uri_search is not None or track_url_search is not None:
        track_id_str = (track_uri_search
                        if track_uri_search is not None else
                        track_url_search).group("TrackID")
    else:
        track_id_str = None

    if album_uri_search is not None or album_url_search is not None:
        album_id_str = (album_uri_search
                        if album_uri_search is not None else
                        album_url_search).group("AlbumID")
    else:
        album_id_str = None

    if playlist_uri_search is not None or playlist_url_search is not None:
        playlist_id_str = (playlist_uri_search
                           if playlist_uri_search is not None else
                           playlist_url_search).group("PlaylistID")
    else:
        playlist_id_str = None

    if episode_uri_search is not None or episode_url_search is not None:
        episode_id_str = (episode_uri_search
                          if episode_uri_search is not None else
                          episode_url_search).group("EpisodeID")
    else:
        episode_id_str = None

    if show_uri_search is not None or show_url_search is not None:
        show_id_str = (show_uri_search
                       if show_uri_search is not None else
                       show_url_search).group("ShowID")
    else:
        show_id_str = None

    if artist_uri_search is not None or artist_url_search is not None:
        artist_id_str = (artist_uri_search
                         if artist_uri_search is not None else
                         artist_url_search).group("ArtistID")
    else:
        artist_id_str = None

    return track_id_str, album_id_str, playlist_id_str, episode_id_str, show_id_str, artist_id_str

