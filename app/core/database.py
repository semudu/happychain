import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling

from .model.constants import Globals
from .utils import hash_password, convert_to_date


class Database:
    def __init__(self, config):
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(host=config.DB_HOST,
                                                                               port=config.DB_PORT,
                                                                               database=config.DB_NAME,
                                                                               user=config.DB_USER,
                                                                               password=config.DB_PASSWD,
                                                                               charset="utf8",
                                                                               pool_size=3)

        except Error as e:
            print("Error while connecting to MySQL", e)

    def __fetchone(self, sql: str, params: tuple = ()) -> dict:
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute(sql, params)
                result = cursor.fetchone()
                return result if result[0] else None
            else:
                raise Exception("Connection is not connected!")
        except Error as e:
            raise e
        finally:
            if conn is not None and conn.is_connected():
                cursor.close()
                conn.close()

    def __fetchall(self, sql: str, params: tuple = ()) -> dict:
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute(sql, params)
                row_headers = [x[0] for x in cursor.description]
                row_values = cursor.fetchall()
                json_result = []
                for result in row_values:
                    json_result.append(dict(zip(row_headers, result)))

                return json_result
            else:
                raise Exception("Connection is not connected!")
        except Error as e:
            raise e
        finally:
            if conn is not None and conn.is_connected():
                cursor.close()
                conn.close()

    def __execute(self, sql: str, params: tuple, insert: bool) -> object:
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                result = cursor.execute(sql, params)
                conn.commit()
                if insert:
                    return cursor.lastrowid
                else:
                    return result

            else:
                raise Exception("Connection is not connected!")
        except Error as e:
            raise e
        finally:
            if conn is not None and conn.is_connected():
                cursor.close()
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
        sql = "insert into user (msisdn, first_name, last_name, gender, date_of_birth, passwd, team_id) values (%s,upper(%s),upper(%s),%s,%s,%s,%s);"
        user_id = self.__execute(sql, (
            msisdn, first_name, last_name, gender, convert_to_date(date_of_birth, "%d.%m.%Y"), hash_password(passwd),
            team_id), True)
        # keys = get_keys()
        # sql = "insert into wallet (wallet_key,public_key,private_key,user_id) values (%s,%s,%s,%s);"
        # wallet_id = self.__execute(sql, (keys['wallet_key'], keys['public_key'], keys['private_key'], user_id), True)
        sql = "insert into wallet (user_id, balance) values (%s%s);"
        wallet_id = self.__execute(sql, (user_id, Globals.LOAD_BALANCE_AMOUNT))
        return {
            "user_id": user_id,
            "wallet_id": wallet_id
        }

    def delete_user(self, identity):
        sql = "delete from user where id = %s"
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

    def get_users_by_scope(self, user_id, start_with=""):
        return self.__fetchall(
            "select u.*, concat(u.first_name,' ', u.last_name) as full_name from user u, team t, scope s where "
            "s.id = t.scope_id "
            "and t.id = u.team_id "
            "and u.id != %s "
            "and s.id = (select scope_id from user where id = %s) "
            "and first_name like %s", (user_id, user_id, start_with + "%"))

    def get_user_id_by_msisdn(self, msisdn):
        user = self.__fetchall("select * from user where msisdn = %s", (msisdn,))
        if len(user) > 0:
            return user[0]["id"]
        return -1

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
        sql = 'select distinct u.full_name, r.text, date_format(t.transaction_date,"%d %M, %W") date from transaction t, user u, reason r where t.receiver_id = u.id and t.reason_id = r.id and t.is_active = 1 and t.sender_id = %s order by t.transaction_date desc limit %s;'
        return self.__fetchall(sql, (user_id, count))

    def get_lastn_received(self, user_id, count):
        sql = 'select distinct u.full_name, r.text, date_format(t.transaction_date,"%d %M, %W") date from transaction t, user u, reason r where t.sender_id = u.id and t.reason_id = r.id and t.is_active = 1 and t.receiver_id = %s order by t.transaction_date desc limit %s;'
        return self.__fetchall(sql, (user_id, count))

    def get_reasons_by_scope(self, scope_id):
        sql = "select * from reason where " \
              "active=1 " \
              "and scope_id = %s " \
              "and (special_date is null or special_date = CURRENT_DATE()) " \
              "order by special_date desc, id asc;"
        return self.__fetchall(sql, (scope_id,))

    def get_reason_by_id(self, reason_id):
        result = self.__fetchone("select text from reason where id = %s;", (reason_id,))
        return result[0] if result else None

    def get_balance(self, user_id):
        result = self.__fetchone("select balance from wallet where user_id = %s;", (user_id,))
        return float(result[0]) if result else 0

    def transfer_points(self, sender_id, receiver_id, reason_id):
        try:
            conn = self.connection_pool.get_connection()

            if conn.is_connected():
                cursor = conn.cursor(prepared=True)
                cursor.execute(
                    "insert into transaction (sender_id, receiver_id, amount, transaction_date, reason_id, is_active) values (%s,%s,%s,CURRENT_TIMESTAMP(),%s,1);"
                    , (sender_id, receiver_id, Globals.SEND_AMOUNT, reason_id))

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
            "select count(*) from transaction where sender_id = %s and receiver_id = %s and transaction_date = curdate() and is_active = 1;",
            (sender_id, receiver_id))
        if count is not None and count[0] > Globals.SEND_SAME_PERSON_LIMIT:
            return False

        return True

    def check_team_limit(self, sender_id, receiver_id):
        count = self.__fetchone(
            "select count(*) from transaction t, user u "
            "where t.sender_id = u.id "
            "and t.transaction_date = curdate() "
            "and t.is_active = 1 "
            "and t.sender_id = %s "
            "and u.team_id = (select team_id from user where id = %s)", (sender_id, receiver_id,))
        if count is not None and count[0] > Globals.SEND_SAME_TEAM_LIMIT:
            return False

        return True

    def get_message(self, scope_id, message_name):
        result = self.__fetchone("select text from message where scope_id= %s and name = %s "
                                 "union all "
                                 "select text from message where scope_id = 0 and name = %s and not exist("
                                 "select * from message where scope_id = %s and name = %s)",
                                 (scope_id, message_name, message_name, scope_id, message_name))

        return result[0] if result else ""
