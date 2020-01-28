import logging
import time

import pycron
import schedule

from .core.model.constants import Globals

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class Job:
    def __init__(self, config):
        self.config = config

    def __load_balance_job(self):
        if pycron.is_now(Globals.LOAD_BALANCE_CRON):
            logging.debug("load balance")

    def _reset_balance_job(self):
        if pycron.is_now(Globals.RESET_BALANCE_CRON):
            logging.debug("reset balance")

    def __special_dates_job(self):
        logging.debug("special dates")

    def __birthday_job(self):
        logging.debug("birthday")

    def send_periodically_messages(self):
        try:
            schedule.every().day.at(Globals.SPECIAL_DATE_MSG_TIME).do(self.__special_dates_job)
            schedule.every().day.at(Globals.BIRTHDAY_MSG_TIME).do(self.__birthday_job)
            schedule.every().day.at(Globals.LOAD_BALANCE_TIME).do(self.__load_balance_job)
            schedule.every().day.at(Globals.RESET_BALANCE_TIME).do(self._reset_balance_job)

            while True:
                schedule.run_pending()
                time.sleep(1)
        except Exception as e:
            logging.error("send_periodically_message: " + str(e))
