from decimal import *

from config import DB

import json
import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling

from app.common.utils import hash_password, convert_to_date
from app.common.constants.globals import *
from app.common.models.free_message import FreeMessage
from app.common.constants.queries import SQL
from app.common.cache import *

from app.common.log import get_logger

logger = get_logger(__name__)


class Database:
    def __init__(self):
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(host=DB.HOST,
                                                                               port=DB.PORT,
                                                                               database=DB.NAME,
                                                                               user=DB.USER,
                                                                               password=DB.PASSWD,
                                                                               charset="utf8",
                                                                               pool_size=5,
                                                                               pool_reset_session=True)


        except Error as e:
            print("Error while connecting to MySQL", e)

    def __fetchone(self, sql: str, params: tuple = ()) -> dict:
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute('SET NAMES utf8mb4')
                cursor.execute("SET CHARACTER SET utf8mb4")
                cursor.execute("SET character_set_connection=utf8mb4")
                cursor.execute(sql, params)
                result = cursor.fetchone()
                cursor.close()

                return result[0] if result else None
            else:
                raise Exception("Connection is not connected!")
        except Error as e:
            raise e
        finally:
            if conn is not None:
                conn.close()

    def __fetchall_with_headers(self, sql: str, params: tuple = ()):
        try:
            conn = self.connection_pool.get_connection()
            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute("SET lc_time_names = 'tr_TR';")
                cursor.execute("SET NAMES utf8mb4")
                cursor.execute("SET CHARACTER SET utf8mb4")
                cursor.execute("SET character_set_connection=utf8mb4")
                cursor.execute(sql, params)
                row_headers = [x[0] for x in cursor.description]
                row_values = cursor.fetchall()
                result = json.loads(json.dumps(row_values))
                result.insert(0, row_headers)
                cursor.close()
                return result
            else:
                raise Exception("Connection is not connected!")
        except Error as e:
            raise e
        finally:
            if conn is not None:
                conn.close()

    def __fetchall(self, sql: str, params: tuple = ()) -> dict:
        try:
            conn = self.connection_pool.get_connection()
            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute("SET lc_time_names = 'tr_TR';")
                cursor.execute("SET NAMES utf8mb4")
                cursor.execute("SET CHARACTER SET utf8mb4")
                cursor.execute("SET character_set_connection=utf8mb4")
                cursor.execute(sql, params)
                row_headers = [x[0] for x in cursor.description]
                row_values = cursor.fetchall()
                cursor.close()
                json_result = []
                for result in row_values:
                    json_result.append(dict(zip(row_headers, result)))
                return json_result
            else:
                raise Exception("Connection is not connected!")
        except Error as e:
            raise e
        finally:
            if conn is not None:
                conn.close()

    def __execute(self, sql: str, params: tuple, insert: bool) -> object:
        try:
            conn = self.connection_pool.get_connection()
            result = None
            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute('SET NAMES utf8mb4')
                cursor.execute("SET CHARACTER SET utf8mb4")
                cursor.execute("SET character_set_connection=utf8mb4")
                result = cursor.execute(sql, params)
                conn.commit()
                if insert:
                    last_row_id = cursor.lastrowid
                    cursor.close()
                    return last_row_id
                else:
                    cursor.close()
                    return result

            else:
                raise Exception("Connection is not connected!")
        except Error as e:
            raise e
        finally:
            if conn is not None:
                conn.close()

    def add_scope(self, scope_name):
        return self.__execute(SQL.ADD_SCOPE, (scope_name,), True)

    def update_scope(self, scope_name, scope_id):
        return self.__execute(SQL.UPDATE_SCOPE, (scope_name, scope_id), False)

    def delete_scope(self, scope_id):
        return self.__execute(SQL.DELETE_SCOPE, (scope_id,), False)

    def add_team(self, team_name, scope_id):
        return self.__execute(SQL.ADD_TEAM, (team_name, scope_id), True)

    def update_team(self, team_id, team_name, scope_id):
        return self.__execute(SQL.UPDATE_TEAM, (team_name, scope_id, team_id), False)

    def delete_team(self, team_id):
        return self.__execute(SQL.DELETE_TEAM, (team_id,), False)

    def get_teams(self):
        return self.__fetchall(SQL.GET_TEAMS)

    def get_team_id_by_name(self, team_name):
        result = self.__fetchone(SQL.GET_TEAM_ID_BY_NAME, (team_name,))
        return result if result else None

    def get_scopes(self):
        return self.__fetchall(SQL.GET_SCOPES)
    
    def get_scope_admins(self):
        return self.__fetchall(SQL.GET_SCOPE_ADMINS)

    def get_scope_by_user_id(self, user_id):
        result = self.__fetchall(SQL.GET_SCOPE_BY_USER_ID, (user_id,))
        return result[0] if len(result) > 0 else -1

    def get_scope_id_by_user_id(self, user_id):
        scope = self.get_scope_by_user_id(user_id)
        return scope["id"] if scope != -1 else scope

    def add_user(self, msisdn, first_name, last_name, gender, date_of_birth, passwd, team_id):
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute(SQL.ADD_USER, (
                    msisdn, first_name, last_name, gender, convert_to_date(date_of_birth, "%d.%m.%Y"),
                    hash_password(passwd),
                    team_id,
                    Role.USER))

                user_id = cursor.lastrowid

                cursor.execute(SQL.ADD_WALLET,
                               (user_id, Globals.LOAD_BALANCE_AMOUNT))

                wallet_id = cursor.lastrowid

                conn.commit()

        except mysql.connector.Error as e:
            conn.rollback()
            raise e
        finally:
            if conn is not None and conn.is_connected():
                cursor.close()
                conn.close()

        return {
            "user_id": user_id,
            "wallet_id": wallet_id
        }

    def delete_user(self, identity):
        return self.__execute(SQL.DELETE_USER, (identity,), False)

    def get_user_by_id(self, identity):
        user = Cache.get(Keys.USER_BY_ID % identity)
        if user is None:
            result = self.__fetchall(SQL.GET_USER_BY_ID, (identity,))
            if len(result) > 0:
                user = result[0]
                Cache.put(Keys.USER_BY_ID % identity, user)

        return user

    def get_user_by_msisdn(self, msisdn):
        user = Cache.get(Keys.USER_BY_MSISDN % msisdn)
        if user is None:
            result = self.__fetchall(SQL.GET_USER_BY_MSISDN, (msisdn,))
            if len(result) > 0:
                user = result[0]
                Cache.put(Keys.USER_BY_MSISDN % msisdn, user)

        return user

    def get_users(self, start_with=""):
        return self.__fetchall(SQL.GET_USERS_LIKE_NAME, (start_with + "%",))

    def get_all_msisdn_list(self):
        return self.__fetchall(SQL.GET_USERS_MSISDN_LIST)

    def get_scope_users_by_user_id_and_like_name(self, user_id, start_with="", offset=0, limit=18446744073709551615):
        return self.__fetchall(SQL.GET_SCOPE_USERS_BY_USER_ID_AND_LIKE_NAME,
                               (user_id, user_id, start_with + "%", "% " + start_with + "%", offset, limit))

    def get_user_id_by_msisdn(self, msisdn):
        user_id = Cache.get(Keys.USER_ID_BY_MSISDN % msisdn)
        if user_id is None:
            user_id = self.__fetchone(SQL.GET_USER_ID_BY_MSISDN, (msisdn,))
            Cache.put(Keys.USER_ID_BY_MSISDN % msisdn, user_id)

        return user_id

    def get_birthday_users(self):
        return self.__fetchall(SQL.GET_BIRTHDAY_USERS)

    def get_wallet_by_user_id(self, user_id):
        wallet = self.__fetchall(SQL.GET_WALLET_BY_USER_ID, (user_id,))
        if len(wallet) > 0:
            return wallet[0]
        return -1

    def get_total_sent_transaction(self, user_id):
        result = self.__fetchone(SQL.GET_TOTAL_SENT, (user_id,))
        return result if result else 0

    def get_total_received_transaction(self, user_id):
        result = self.__fetchone(SQL.GET_TOTAL_RECEIVED, (user_id,))
        return result if result else 0

    def get_last_n_sent(self, user_id, count):
        return self.__fetchall(SQL.GET_LAST_N_SENT, (user_id, count))

    def get_last_n_received(self, user_id, count):
        return self.__fetchall(SQL.GET_LAST_N_RECEIVED, (user_id, count))

    def get_message_list_by_user_id(self, user_id):
        messages = Cache.get(Keys.MESSAGE_LIST_BY_USER_ID % user_id)
        if messages is None:
            messages = self.__fetchall(SQL.GET_MESSAGE_LIST_BY_USER_ID, (user_id, user_id, user_id))
            Cache.put(Keys.MESSAGE_LIST_BY_USER_ID % user_id, messages)

        return messages

    def get_message_by_id(self, message_id):
        message = Cache.get(Keys.MESSAGE_BY_ID % message_id)
        if message is None:
            message = self.__fetchone(SQL.GET_MESSAGE_BY_ID, (message_id,))
            Cache.put(Keys.MESSAGE_BY_ID, message)

        return message

    def get_balance_by_user_id(self, user_id):
        result = self.__fetchone(SQL.GET_BALANCE_BY_USER_ID, (user_id,))
        return Decimal(result) if result else 0

    def transfer_points(self, sender_id, receiver_id, message_id, free_message=None):
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute(SQL.ADD_TRANSACTION,
                               (sender_id, receiver_id, Globals.SEND_AMOUNT, message_id, free_message))
                cursor.execute(SQL.REMOVE_BALANCE_BY_USER, ((Globals.SEND_AMOUNT - Globals.EARN_AMOUNT), sender_id))
                cursor.execute(SQL.ADD_BALANCE_BY_USER, (Globals.SEND_AMOUNT, receiver_id))
                conn.commit()

        except mysql.connector.Error as e:
            conn.rollback()
            raise e
        finally:
            if conn is not None and conn.is_connected():
                cursor.close()
                conn.close()

    def check_user_limit(self, sender_id, receiver_id) -> bool:
        count = self.__fetchone(SQL.GET_USER_SENT_COUNT_BY_RECEIVER_TODAY, (sender_id, receiver_id))
        if count is not None and count > Globals.SEND_SAME_PERSON_LIMIT:
            return False
        return True

    def check_team_limit(self, sender_id, receiver_id):
        count = self.__fetchone(SQL.GET_USER_SENT_COUNT_BY_RECEIVER_TEAM_TODAY, (sender_id, receiver_id,))
        if count is not None and count > Globals.SEND_SAME_TEAM_LIMIT:
            return False
        return True

    def get_birthday_message(self):
        return self.__fetchone(SQL.GET_BIRTHDAY_MESSAGE)

    def get_special_dates(self):
        return self.__fetchall(SQL.GET_SPECIAL_DATES)

    def check_free_message(self, user_id):
        last_transaction = self.__fetchall(SQL.GET_USER_LAST_TRANSACTION_BY_EMPTY_MESSAGE_TODAY, (user_id,))
        if last_transaction:
            return last_transaction[0]
        return None

    def insert_free_message(self, transaction, msg_type, message):
        free_msg = FreeMessage(msg_type, message).get_json_str()
        self.__execute(SQL.UPDATE_FREE_MESSAGE, (free_msg, transaction["id"]), False)

        return transaction

    def load_balance_user(self, user_id, amount):
        return self.__execute(SQL.ADD_BALANCE_BY_USER, (amount, user_id), False)

    def load_balance_all(self, amount):
        return self.__execute(SQL.ADD_BALANCE_ALL, (amount,), False)

    def reset_balance_all(self, amount):
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute(SQL.UPDATE_BALANCE_ALL, (amount,))
                cursor.execute(SQL.ARCHIVE_ACTIVE_TRANSACTIONS)
                cursor.execute(SQL.TRUNCATE_TRANSACTIONS)
                conn.commit()

        except mysql.connector.Error as e:
            conn.rollback()
            raise e
        finally:
            if conn is not None and conn.is_connected():
                cursor.close()
                conn.close()

    def get_received_messages_by_team(self, team_id, limit):
        return self.__fetchall(SQL.GET_LAST_N_RECEIVED_MESSAGES_BY_TEAM, (team_id, limit))

    def get_transaction_count_by_scope(self, scope_id):
        count = self.__fetchone(SQL.GET_TRANSACTION_COUNT_BY_SCOPE, (scope_id,))
        if count is not None:
            return count
        return 0

    def get_top_ten_user_by_scope(self, scope_id):
        return self.__fetchall(SQL.GET_TOP_TEN_USER_BY_SCOPE, (Globals.EARN_AMOUNT, Globals.SEND_AMOUNT, scope_id))

    def get_sent_user_list_by_scope(self, scope_id):
        return self.__fetchall_with_headers(SQL.GET_SENT_USER_LIST_BY_SCOPE_ID, (scope_id,))

    def get_received_user_list_by_scope(self, scope_id):
        return self.__fetchall_with_headers(SQL.GET_RECEIVED_USER_LIST_BY_SCOPE_ID, (scope_id,))

    def get_top_user_list_by_scope_id(self, scope_id):
        return self.__fetchall_with_headers(SQL.GET_TOP_USER_LIST_BY_SCOPE_ID, (
            Globals.SEND_AMOUNT, Globals.EARN_AMOUNT, scope_id, Globals.SEND_AMOUNT, Globals.EARN_AMOUNT))

    def get_messages_by_scope_id(self, scope_id):
        return self.__fetchall_with_headers(SQL.GET_MESSAGES_BY_SCOPE_ID, (scope_id,))
