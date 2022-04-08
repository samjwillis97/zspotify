import json
import requests
from pydub import AudioSegment
from librespot.audio.decoders import AudioQuality

import helpers
import load_env as env


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


def get_episode_info(user_read_email_token, episode_id_str):
    """ Get Podcast Episode Info  """
    info = json.loads(requests.get(
        "https://api.spotify.com/v1/episodes/" +
            episode_id_str, headers={
                "Authorization": f"Bearer {user_read_email_token}"
            }).text)
    if "error" in info:
        return None, None
    return helpers.sanitize_data(info["show"]["name"]), helpers.sanitize_data(info["name"])

