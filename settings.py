import os


class Settings:
    DEBUG = False
    SECRET_KEY = "njkasdjadkhasda"
    LOG_LEVEL = "debug"
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    APP_NAME = 'HappyChain'
    HOST = '0.0.0.0'
    PORT = os.environ.get('PORT', 5000)
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT')
    DB_NAME = os.environ.get('DB_NAME')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWD = os.environ.get('DB_PASSWD')
    BIP_URL = os.environ.get('BIP_URL')
    BIP_USERNAME = os.environ.get('BIP_USERNAME')
    BIP_PASSWORD = os.environ.get('BIP_PASSWORD')
    TRANSFER_SECRET = os.environ.get('TRANSFER_SECRET')
    BASIC_AUTH_USERNAME = os.environ.get('BASIC_AUTH_USERNAME')
    BASIC_AUTH_PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD')
    BASIC_AUTH_FORCE = False
    BASIC_AUTH_REALM = os.environ.get('BASIC_AUTH_REALM')
