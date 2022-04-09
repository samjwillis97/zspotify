"""
CLI Interface Handler
"""

def handle(args: list) -> None:
    """ handles CLI input """
    if args[1] == "search":
        search_string()
    elif args[1] == "-p" or args[1] == "--playlist":
        playlist()
    elif args[1] == "-ls" or args[1] == "--liked-songs":
        liked_songs()
    elif args[1] == "-w" or args[1] == "--web":
        web_server()
    elif args[1] == "-h" or args[1] == "--help":
        help()
    else:
        unrecognized()

def playlist():
    pass

def liked_songs():
    pass

def web_server():
    pass

def search_string():
    pass

def help():
    pass

def unrecognized():
    pass
