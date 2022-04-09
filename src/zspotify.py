#! /usr/bin/env python3

"""
ZSpotify
It's like youtube-dl, but for Spotify.
"""
import sys

import helpers
import auth
import spotify_api
import cli

def main():
    """ Main Function """
    # Pretty Printout
    helpers.splash()
    
    # Login to Spotify and get the Client
    client = auth.Client()
    spotify = spotify_api.Spotify(client)

    # Command Line Argument Given
    cli.handle(spotify, sys.argv)


if __name__ == "__main__":
    main()
