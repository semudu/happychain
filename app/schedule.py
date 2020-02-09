import json
import logging
import threading
import time

import pycron
import schedule
from bipwrapper.api import API

from app.models.constants import Globals
from app.services.utils import get_name_with_own_suffix
from settings import Settings
from .services.database import Database

logging.basicConfig(format='%(levelname)s-%(thread)d:%(message)s', level=logging.DEBUG)


class Schedule(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name="jobs-thread")
        self.db = Database()
        self.bip_api = API(Settings.BIP_URL, Settings.BIP_USERNAME, Settings.BIP_PASSWORD)
        return

    def __load_balance_job(self):
        try:
            if pycron.is_now(Globals.LOAD_BALANCE_CRON):
                self.db.load_balance_all(Globals.LOAD_BALANCE_AMOUNT)
                # TODO all message
        except Exception as e:
            logging.error("An error occured in load balance job: " + str(e))

    def _reset_balance_job(self):
        try:
            if pycron.is_now(Globals.RESET_BALANCE_CRON):
                self.db.reset_balance_all(Globals.LOAD_BALANCE_AMOUNT)
                # TODO all message

        except Exception as e:
            logging.error("An error occured in reset balance job: " + str(e))

    def __special_dates_job(self):
        try:
            special_date_messages = self.db.get_special_dates()
            if len(special_date_messages) > 0:
                logging.debug("special dates")


        except Exception as e:
            logging.error("An error occured in special date job: " + str(e))

    def __birthday_job(self):
        try:
            users = self.db.get_birthday_users()
            if len(users) > 0:
                for user in users:
                    scope_id = self.db.get_user_scope_id(user["id"])
                    message = self.db.get_out_message(scope_id, 'D')
                    if len(message) > 0:
                        target_users = self.db.get_users_by_scope(user["id"])
                        if len(target_users) > 0:
                            message_json = json.loads(message[0]["text"])
                            receivers = []
                            for target_user in target_users:
                                if target_user["id"] != user["id"]:
                                    receivers.append(target_user["msisdn"])
                            if len(receivers) > 0:
                                self.bip_api.multi.send_text_message(receivers, message_json[
                                    "message"] % get_name_with_own_suffix(
                                    user["full_name"]))

        except Exception as e:
            logging.error("An error occured in birthday job: " + str(e))


def __reminder_job(self):
    try:
        logging.debug("send reminder to deactive users")
    except Exception as e:
        logging.error("An error occured in reminder job: " + str(e))


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
