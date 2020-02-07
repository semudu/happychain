import logging
import threading
import time

import pycron
import schedule

from app.models.constants import Globals
from .services.database import Database

logging.basicConfig(format='%(levelname)s-%(thread)d:%(message)s', level=logging.DEBUG)


class Schedule(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name="jobs-thread")
        self.db = Database()
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
        for user in users:
            logging.debug(user["full_name"])

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
