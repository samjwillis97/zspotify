import os
from distutils.util import strtobool
from dotenv import load_dotenv
from loguru import logger

def is_docker():
    path = '/proc/self/cgroup'
    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
    )

if not is_docker():
    logger.info("Loading .env File")
    load_dotenv()

# READ ENV
DEBUG = bool(strtobool(os.getenv("DEBUG", "False")))

# Download Paths
ROOT_PATH = "/download/zspotify_music/"
ROOT_PODCAST_PATH = "zspotify_podcasts/" # TODO: Is this right?

SKIP_EXISTING_FILES = bool(strtobool(os.getenv("SKIP_EXISTING_FILES", "True")))

# mp3 or ogg 
MUSIC_FORMAT = os.getenv('MUSIC_FORMAT', "mp3")

# set to True if not detecting your premium account automaticalllyg
FORCE_PREMIUM = bool(strtobool(os.getenv("FORCE_PREMIUM", "False")))
RAW_AUDIO_AS_IS = bool(strtobool(os.getenv('RAW_AUDIO_AS_IS', "False")))

# This is how many seconds ZSpotify waits between downloading tracks so
# spotify doesn't get out the ban hammer
ANTI_BAN_WAIT_TIME = int(os.getenv("ANTI_BAN_WAIT_TIME", "5"))
ANTI_BAN_WAIT_TIME_ALBUMS = int(os.getenv("ANTI_BAN_WAIT_TIME_ALBUMS", "30"))
# Set this to True to not wait at all between tracks and just go balls to the wall
OVERRIDE_AUTO_WAIT = bool(strtobool(os.getenv("OVERRIDE_AUTO_WAIT", "False")))

CHUNK_SIZE = 50000
LIMIT = 50
DEFAULT_RETRIES = 10

# if DEBUG:
#     logger.info("DEBUG Mode Started")

