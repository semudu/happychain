from decimal import *

import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling

from app.models.constants import Globals, Role
from settings import Settings
from .utils import hash_password, convert_to_date


class Database:
    def __init__(self):
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(host=Settings.DB_HOST,
                                                                               port=Settings.DB_PORT,
                                                                               database=Settings.DB_NAME,
                                                                               user=Settings.DB_USER,
                                                                               password=Settings.DB_PASSWD,
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

    def __fetchall(self, sql: str, params: tuple = ()) -> dict:
        try:
            conn = self.connection_pool.get_connection()
            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute('SET NAMES utf8mb4')
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
        sql = "insert into scope (`name`) values (%s);"
        return self.__execute(sql, (scope_name,), True)

    def update_scope(self, scope_name, scope_id):
        sql = "update scope set name = %s where id = %s;"
        return self.__execute(sql, (scope_name, scope_id), False)

    def delete_scope(self, scope_id):
        sql = "delete from scope where id = %s;"
        return self.__execute(sql, (scope_id,), False)

    def add_team(self, team_name, scope_id):
        sql = "insert into team (`name`,`scope_id`) values (%s,%s);"
        return self.__execute(sql, (team_name, scope_id), True)

    def update_team(self, team_id, team_name, scope_id):
        sql = "update team set name = %s, scope_id = %s where id = %s;"
        return self.__execute(sql, (team_name, scope_id, team_id), False)

    def delete_team(self, team_id):
        sql = "delete from team where id = %s;"
        return self.__execute(sql, (team_id,), False)

    def get_teams(self):
        sql = "select * from team;"
        return self.__fetchall(sql)

    def get_team_id_by_name(self, team_name):
        result = self.__fetchone("select id from team where name = %s", (team_name,))
        return result if result else None

    def get_scopes(self):
        sql = "select * from scope;"
        return self.__fetchall(sql)

    def get_user_scope_id(self, user_id):
        sql = "select s.* from scope s, team t, user u where " \
              "t.scope_id = s.id " \
              "and u.team_id = t.id " \
              "and u.id = %s;"
        result = self.__fetchall(sql, (user_id,))
        return len(result) > 0 if result[0]["id"] else -1

    def add_user(self, msisdn, first_name, last_name, gender, date_of_birth, passwd, team_id):
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                sql = "insert into user (msisdn, first_name, last_name, gender, date_of_birth, passwd, team_id, role) values (%s,upper(%s),upper(%s),%s,%s,%s,%s,%s);"
                cursor.execute(sql, (
                    msisdn, first_name, last_name, gender, convert_to_date(date_of_birth, "%d.%m.%Y"),
                    hash_password(passwd),
                    team_id,
                    Role.USER))

                user_id = cursor.lastrowid

                sql = "insert into wallet (user_id, balance) values (%s,%s);"
                cursor.execute(sql,
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
        sql = "update user set active = 0 where id = %s"
        return self.__execute(sql, (identity,), False)

    def get_user_by_id(self, identity):
        result = self.__fetchall(
            "select u.*, concat(u.first_name,' ', u.last_name) as full_name from user u where id = %s", (identity,))
        if len(result) > 0:
            return result[0]
        return None

    def get_users(self, start_with=""):
        return self.__fetchall(
            "select u.*, concat(u.first_name,' ', u.last_name) as full_name from user u where first_name like %s",
            (start_with + "%",))

    def get_all_msisdn_list(self):
        return self.__fetchall("select msisdn from user")

    def get_users_by_scope(self, user_id, start_with=""):
        return self.__fetchall(
            "select u.*, concat(u.first_name, ' ', u.last_name) as full_name from user u "
            "where u.id != %s "
            "and u.team_id in (select id from team "
            "where scope_id = (select s.id from scope s, team t, user u "
            "where u.team_id = t.id and t.scope_id = s.id and u.id = %s)) and first_name like %s;",
            (user_id, user_id, start_with + "%"))

    def get_user_id_by_msisdn(self, msisdn):
        user_id = self.__fetchone("select id from user where msisdn = %s", (msisdn,))
        return user_id if user_id else None

    def get_birthday_users(self):
        return self.__fetchall(
            "select u.*, concat(u.first_name,' ', u.last_name) as full_name from user u where dayofmonth(date_of_birth) = dayofmonth(curdate()) and month(date_of_birth) = month(curdate());")

    def get_wallet_by_userid(self, user_id):
        wallet = self.__fetchall("select * from wallet where user_id = %s", (user_id,))
        if len(wallet) > 0:
            return wallet[0]
        return -1

    def get_total_sent_transaction(self, user_id):
        result = self.__fetchone(
            "SELECT sum(amount) total_sent FROM transaction WHERE is_active = 1 and sender_id = %s",
            (user_id,))
        return result if result else 0

    def get_total_received_transaction(self, user_id):
        result = self.__fetchone(
            "SELECT sum(amount) total_received FROM transaction WHERE is_active = 1 and receiver_id = %s",
            (user_id,))
        return result if result else 0

    def get_lastn_sent(self, user_id, count):
        sql = 'select distinct u.full_name, m.text, date_format(t.date,"%d %M, %W") date from transaction t, user u, message m where t.receiver_id = u.id and t.message_id = r.id and t.is_active = 1 and t.sender_id = %s order by t.date desc limit %s;'
        return self.__fetchall(sql, (user_id, count))

    def get_lastn_received(self, user_id, count):
        sql = 'select distinct u.full_name, m.text, date_format(t.date,"%d %M, %W") date from transaction t, user u, message m where t.sender_id = u.id and t.message_id = r.id and t.is_active = 1 and t.receiver_id = %s order by t.date desc limit %s;'
        return self.__fetchall(sql, (user_id, count))

    def get_message_list_by_target(self, target_user_id):
        sql = "select r.id, r.text from ( select * from message where direction = 'IN' and type = 'D' and exists(select * from user u where dayofmonth(date_of_birth) = dayofmonth(curdate()) and month(date_of_birth) = month(curdate()) and id = %s) union select * from message where direction = 'IN' and SPLIT_STRING(date, '/', 1) = dayofmonth(curdate()) and SPLIT_STRING(date, '/', 2) = month(curdate()) and (type is null or type = (select gender from user where id = %s)) union select m.* from message m, team t, user u where u.id = %s and u.team_id = t.id and m.direction = 'IN' and (m.type is null or m.type in ('K', 'E')) and m.date is null and ((exists(select * from message where scope_id = t.scope_id) and m.scope_id = t.scope_id) or (not exists(select * from message where scope_id = t.scope_id) and m.scope_id = 0))) r order by r.date desc, r.type desc, r.id asc limit 6;"

        return self.__fetchall(sql, (target_user_id, target_user_id, target_user_id))

    def get_message_by_id(self, message_id):
        result = self.__fetchone("select text from message where id = %s;", (message_id,))
        return result if result else None

    def get_balance(self, user_id):
        result = self.__fetchone("select balance from wallet where user_id = %s;", (user_id,))
        return Decimal(result) if result else 0

    def transfer_points(self, sender_id, receiver_id, message_id):
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute(
                    "insert into transaction (sender_id, receiver_id, amount, date, message_id, is_active) values (%s,%s,%s,CURRENT_TIMESTAMP(),%s,1);"
                    , (sender_id, receiver_id, Globals.SEND_AMOUNT, message_id))

                cursor.execute("update wallet set balance = balance - %s where user_id = %s",
                               (Globals.SEND_AMOUNT - Globals.EARN_AMOUNT, sender_id))

                cursor.execute("update wallet set balance = balance + %s where user_id = %s",
                               (Globals.SEND_AMOUNT, receiver_id))

                conn.commit()

        except mysql.connector.Error as e:
            conn.rollback()
            raise e
        finally:
            if conn is not None and conn.is_connected():
                cursor.close()
                conn.close()

    def check_user_limit(self, sender_id, receiver_id) -> bool:
        count = self.__fetchone(
            "select count(*) from transaction where sender_id = %s and receiver_id = %s and date = curdate() and is_active = 1;",
            (sender_id, receiver_id))
        if count is not None and count > Globals.SEND_SAME_PERSON_LIMIT:
            return False

        return True

    def check_team_limit(self, sender_id, receiver_id):
        count = self.__fetchone(
            "select count(*) from transaction t, user u "
            "where t.sender_id = u.id "
            "and t.date = curdate() "
            "and t.is_active = 1 "
            "and t.sender_id = %s "
            "and u.team_id = (select team_id from user where id = %s)", (sender_id, receiver_id,))
        if count is not None and count > Globals.SEND_SAME_TEAM_LIMIT:
            return False

        return True

    def get_special_dates(self):
        return self.__fetchall(
            "select * from message where direction = 'OUT' and type='S' and scope_id = 0 and split_string(date,'/',1) = dayofmonth(curdate()) and split_string(date,'/',2) = month(curdate())")

    def get_out_message(self, scope_id, message_type):
        return self.__fetchall("select text from message where scope_id=%s and type=%s and direction='OUT'"
                               "union all "
                               "select text from message where scope_id=0 and type=%s and direction='OUT' and not exists("
                               "select * from message where scope_id=%s and type=%s and direction='OUT')",
                               (scope_id, message_type, message_type, scope_id, message_type))

    def check_free_message(self, user_id):
        last_transaction = self.__fetchall(
            "select * from transaction where sender_id = %s and is_active = 1 and message_id=-1 and free_message is null and date(date) = date(curdate()) order by id desc limit 1",
            (user_id,))

        if last_transaction:
            return last_transaction[0]

        return None

    def update_free_message(self, transaction, msg_type, message):
        free_message = '{"type":"%s","content":"%s"}' % (msg_type, message)
        sql = "update transaction set free_message = %s where id = %s"
        self.__execute(sql, (free_message, transaction["id"]), False)

        return transaction

    def load_balance_user(self, user_id, amount):
        return self.__execute("update wallet set balance = balance + %s where user_id = %s", (amount, user_id), False)

    def load_balance_all(self, amount):
        return self.__execute("update wallet set balance = balance + %s", (amount,), False)

    def reset_balance_all(self, amount):
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute(
                    "update wallet set balance = %s"
                    , (amount,))

                cursor.execute(
                    "insert into transaction_archive (date, archive_date, sender_id, receiver_id, message_id, free_text, amount) "
                    "select date, curdate(), sender_id, receiver_id, message_id, free_text, amount from transaction where is_active = 1")

                cursor.execute("truncate table transaction")

                conn.commit()

        except mysql.connector.Error as e:
            conn.rollback()
            raise e
        finally:
            if conn is not None and conn.is_connected():
                cursor.close()
                conn.close()
