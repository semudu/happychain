import redis
import pickle


class Keys:
    USER_ID_BY_MSISDN = "user_id--msisdn:%s"
    USER_BY_ID = "user--user_id:%s"
    USER_BY_MSISDN = "user--msisdn:%s"
    MESSAGE_LIST_BY_USER_ID = "message_list--user_id:%s"
    MESSAGE_BY_ID = "message-message_id:%s"
    FREE_MSG_BY_USER_ID = "free_message--user_id:%s"
    ALL_MSG_BY_USER_ID = "all_message--user_id:%s"
    QUICK_REPLY_BY_USER_IDS = "quick_reply--user_ids:%s-%s"


class Cache:
    redis = redis.Redis()

    @staticmethod
    def put(key, value):
        Cache.redis.set(key, pickle.dumps(value))

    @staticmethod
    def get(key):
        if Cache.redis.exists(key):
            return pickle.loads(Cache.redis.get(key))
        return None

    @staticmethod
    def multiple_delete(pattern):
        keys = Cache.redis.keys(pattern)
        for key in keys:
            Cache.delete(key)

    @staticmethod
    def delete(key):
        Cache.redis.delete(key)

    @staticmethod
    def clear():
        Cache.redis.flushall()
