import os
import shutil
from getpass import getpass
from librespot.core import Session
from librespot.audio.decoders import AudioQuality
import load_env as env
from loguru import logger

class Client:
    _session = None
    is_premium = False
    quality = AudioQuality.HIGH

    def __init__(self):
        self._login()

    def session(self):
        """ Returns Client Session """
        return self._session

    # TODO: Pull in username and password from another method
    def _login(self):
        """ Authenticates with Spotify and saves credentials to a file """
        if os.path.isfile("/config/credentials.json"):
            shutil.copyfile('/config/credentials.json', 'credentials.json')

        if os.path.isfile("credentials.json"):
            try:
                self._session = Session.Builder().stored_file().create()
                return
            except RuntimeError:
                pass
        while True:
            user_name = input("Username: ")
            password = getpass()
            try:
                self._session = Session.Builder().user_pass(user_name, password).create()
                shutil.copyfile('credentials.json','/config/credentials.json')
                return
            except RuntimeError:
                pass
        self.is_premium = bool((self._session.get_user_attribute("type") == "premium") or env.FORCE_PREMIUM)
        if self.is_premium:
            # logger.info("Logged into Premium Account - Using Very High Quality")
            self.quality = AudioQuality.VERY_HIGH
        # else:
            # logger.info("Logged into Free Account - Using High Quality")
