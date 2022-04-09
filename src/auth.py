"""
Authentication
This file containts methods to connect, authenticate and get session tokens
from Spotify.

"""

import os
import shutil
from getpass import getpass
from librespot.core import Session
from librespot.audio.decoders import AudioQuality
import load_env as env


class Client:
    """ Client Authenticated by Spotify  """
    _session: Session  = None
    is_premium: bool = False
    quality: AudioQuality = AudioQuality.HIGH

    def __init__(self):
        self._login()
        self._update_user_info()

    # TODO: Pull in username and password from another method
    # Via Web Server possibly?
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

    def _update_user_info(self):
        self.is_premium = bool((self._session.get_user_attribute("type") == "premium") or env.FORCE_PREMIUM)
        if self.is_premium:
            # logger.info("Logged into Premium Account - Using Very High Quality")
            self.quality = AudioQuality.VERY_HIGH
        # else:
        # logger.info("Logged into Free Account - Using High Quality")

    def session(self):
        """ Returns Client Session """
        return self._session

    def user_read_email_token(self):
        """ Returns the 'user-read-email' token for the client """
        return self._session.tokens().get("user-read-email")
    
