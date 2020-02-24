import json

import pycron
import schedule
import time

from bipwrapper import BipWrapper
from bipwrapper.type.poll_type import PollType

from app.commons.log import get_logger
from app.commons.database import Database
from app.commons.utils import *
from app.commons.constants.globals import Globals
from app.commons.constants.message import Message
from app.commons.constants.command import Command
from config import BIP, APP

logger = get_logger(__name__)

db = Database()
bip_api = BipWrapper(BIP.ENVIRONMENT, BIP.USERNAME, BIP.PASSWORD)


def load_balance_job():
    try:
        if pycron.is_now(Globals.LOAD_BALANCE_CRON) and not pycron.is_now(Globals.RESET_BALANCE_CRON):
            db.load_balance_all(Globals.LOAD_BALANCE_AMOUNT)
            receivers = list(map(lambda msisdn: msisdn["msisdn"], db.get_all_msisdn_list()))
            bip_api.multi.send_text_message(receivers, Message.LOAD_BALANCE_MESSAGE % Globals.LOAD_BALANCE_AMOUNT)

    except Exception as e:
        logger.error("An error occured in load balance job: " + str(e))


def reset_balance_job():
    try:
        if pycron.is_now(Globals.RESET_BALANCE_CRON):
            db.reset_balance_all(Globals.LOAD_BALANCE_AMOUNT)
            receivers = list(map(lambda msisdn: msisdn["msisdn"], db.get_all_msisdn_list()))
            bip_api.multi.send_text_message(receivers, Message.RESET_BALANCE_MESSAGE % Globals.LOAD_BALANCE_AMOUNT)

    except Exception as e:
        logger.error("An error occured in reset balance job: " + str(e))


def special_dates_job():
    try:
        special_date_messages = db.get_special_dates()
        if len(special_date_messages) > 0:
            logger.debug("special dates")

    except Exception as e:
        logger.error("An error occured in special date job: " + str(e))


def birthday_job():
    try:
        users = db.get_birthday_users()
        if len(users) > 0:
            for user in users:
                scope_id = db.get_scope_id_by_user_id(user["id"])
                message = db.get_out_message(scope_id, 'D')
                if len(message) > 0:
                    target_users = db.get_scope_users_by_user_id_and_like_name(user["id"])
                    if len(target_users) > 0:
                        message_json = json.loads(message[0]["text"])
                        message_list = db.get_message_list_by_user_id(user["id"])
                        message_tuple = get_key_value_tuple(message_list, "id", "text")
                        for target_user in target_users:
                            if target_user["id"] != user["id"]:
                                bip_api.single.send_poll_message(
                                    target_user["msisdn"],
                                    "%s%s%s%s%s%s%s" % (
                                        Command.FINISH_TRANSACTION, Globals.DELIMITER, str(user["id"]),
                                        Globals.DELIMITER,
                                        str(target_user["id"]),
                                        APP.TRANSFER_SECRET, str(user["id"])),
                                    message_json["title"] % get_name_with_own_suffix(user["full_name"]),
                                    message_json["message"],
                                    message_json["image"],
                                    1,
                                    PollType.SINGLE_CHOOSE,
                                    message_tuple,
                                    "OK")

                        bip_api.single.send_text_message(user["msisdn"],
                                                         Message.BIRTHDAY_MESSAGE % (
                                                             user["first_name"], Globals.LOAD_BALANCE_AMOUNT))
                        db.load_balance_user(user["id"], Globals.LOAD_BALANCE_AMOUNT)

    except Exception as e:
        logger.error("An error occured in birthday job: " + str(e))


def reminder_job():
    try:
        logger.debug("send reminder to deactive users")
    except Exception as e:
        logger.error("An error occured in reminder job: " + str(e))


if __name__ == "__main__":
    try:
        schedule.every().day.at(Globals.SPECIAL_DATE_MSG_TIME).do(special_dates_job)
        schedule.every().day.at(Globals.BIRTHDAY_MSG_TIME).do(birthday_job)
        schedule.every().day.at(Globals.LOAD_BALANCE_TIME).do(load_balance_job)
        schedule.every().day.at(Globals.RESET_BALANCE_TIME).do(reset_balance_job)

        while True:
            schedule.run_pending()
            time.sleep(10)
    except Exception as e:
        logger.error("send_periodically_message: " + str(e))
    finally:
        print("Schedule thread finished.")
