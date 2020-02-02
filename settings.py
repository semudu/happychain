import os


class Settings:
    DEBUG = True
    LOG_LEVEL = "debug"
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    APP_NAME = 'HappyChain'
    HOST = '0.0.0.0'
    PORT = '5000'
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT')
    DB_NAME = os.environ.get('DB_NAME')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWD = os.environ.get('DB_PASSWD')
    BIP_URL = os.environ.get('BIP_URL')
    BIP_USERNAME = os.environ.get('BIP_USERNAME')
    BIP_PASSWORD = os.environ.get('BIP_PASSWORD')
