import json
import logging
import threading
import time

import pycron
import schedule
from bipwrapper.api import Api

from app.models.constants import Globals
from settings import Settings
from .services.database import Database

logging.basicConfig(format='%(levelname)s-%(thread)d:%(message)s', level=logging.DEBUG)


class Schedule(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name="jobs-thread")
        self.db = Database()
        self.bip_api = Api(Settings.BIP_URL, Settings.BIP_USERNAME, Settings.BIP_PASSWORD)
        return

    def __load_balance_job(self):
        if pycron.is_now(Globals.LOAD_BALANCE_CRON):
            logging.debug("load balance")

    def _reset_balance_job(self):
        if pycron.is_now(Globals.RESET_BALANCE_CRON):
            logging.debug("reset balance")

    def __special_dates_job(self):
        logging.debug("special dates")

    def __birthday_job(self):
        users = self.db.get_birthday_users()
        if len(users) > 0:
            for user in users:
                scope_id = self.db.get_user_scope_id(user["id"])
                message = self.db.get_out_message(scope_id, 'D')
                if len(message) > 0:
                    target_users = self.db.get_users_by_scope(user["id"])
                    if len(target_users) > 0:
                        message_json = json.loads(message[0]["text"])
                        for target_user in target_users:
                            if target_user["id"] != user["id"]:
                                self.bip_api.single.send_text_message(target_user["msisdn"],
                                                                      message_json["message"] % user["full_name"])

    def __reminder_job(self):
        logging.debug("send reminder to deactive users")

    def run(self):
        try:
            schedule.every().day.at(Globals.SPECIAL_DATE_MSG_TIME).do(self.__special_dates_job)
            schedule.every().day.at(Globals.BIRTHDAY_MSG_TIME).do(self.__birthday_job)
            schedule.every().day.at(Globals.LOAD_BALANCE_TIME).do(self.__load_balance_job)
            schedule.every().day.at(Globals.RESET_BALANCE_TIME).do(self._reset_balance_job)

            while True:
                schedule.run_pending()
                time.sleep(10)
        except Exception as e:
            logging.error("send_periodically_message: " + str(e))
        finally:
            print("Schedule thread finished.")
