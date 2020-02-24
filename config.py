import yaml

with open("config.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)


class APP:
    DEBUG = cfg["app"]["debug"]
    LOG_LEVEL = cfg["app"]["log_level"]
    LOG_FORMAT = cfg["app"]["log_format"]
    APP_NAME = cfg["app"]["app_name"]
    TRANSFER_SECRET = cfg["app"]["transfer_secret"]


class DB:
    HOST = cfg["db"]["host"]
    PORT = cfg["db"]["port"]
    NAME = cfg["db"]["name"]
    USER = cfg["db"]["user"]
    PASSWD = cfg["db"]["passwd"]


class RedisConf:
    HOST = cfg["redis"]["host"]
    PORT = cfg["redis"]["port"]
    PASSWORD = cfg["redis"]["passwd"]


class BIP:
    ENVIRONMENT = cfg["bip"]["environment"]
    USERNAME = cfg["bip"]["user"]
    PASSWORD = cfg["bip"]["passwd"]


class FlaskConf:
    SECRET_KEY = cfg["flask"]["secret_key"]
    BASIC_AUTH_USERNAME = cfg["flask"]["basic_auth"]["username"]
    BASIC_AUTH_PASSWORD = cfg["flask"]["basic_auth"]["password"]
    BASIC_AUTH_FORCE = cfg["flask"]["basic_auth"]["force"]
    BASIC_AUTH_REALM = cfg["flask"]["basic_auth"]["realm"]
