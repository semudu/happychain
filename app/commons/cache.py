import redis
from config import RedisConf
from app.commons.log import get_logger

logger = get_logger(__name__)


class Cache:
    def __init__(self):
        try:
            self.r = redis.StrictRedis(host=RedisConf.HOST,
                                       port=RedisConf.PORT,
                                       password=RedisConf.PASSWORD,
                                       decode_responses=True)
            self.__up = True
        except Exception as e:
            logger.error("Redis initialize error. ", str(e))
            self.__up = False

    def is_up(self):
        return self.__up

    def get(self, key):
        if self.__up:
            return 0
        return None

    def set(self, key):
        if self.__up:
            # TODO
            pass
