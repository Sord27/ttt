import os

APP_DIR = os.path.split(os.path.abspath(__file__))[0]
CONFIG = os.path.join(APP_DIR, 'config.ini')

# config.ini sections
SUMO_CREDENTIALS = 'sumo_credentials'
