import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling

from .utils import hash_password, get_keys


class Database:
    def __init__(self, config):
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(host=config.DB_HOST,
                                                                               port=config.DB_PORT,
                                                                               database=config.DB_NAME,
                                                                               user=config.DB_USER,
                                                                               password=config.DB_PASSWD,
                                                                               charset="utf8mb4",
                                                                               autocommit=True,
                                                                               pool_size=3)
        except Error as e:
            print("Error while connecting to MySQL", e)

    def __fetchone(self, sql: str, input: tuple = ()) -> dict:
        try:
            connection_object = self.connection_pool.get_connection()

            if connection_object.is_connected():
                cursor = connection_object.cursor(prepared=True)
                cursor.execute(sql, input)
                result = cursor.fetchone()
                return result if result[0] else None
            else:
                raise Exception("Connection is not connected!")
        except Error as e:
            raise e
        finally:
            if (connection_object.is_connected()):
                cursor.close()
                connection_object.close()

    def __fetchall(self, sql: str, input: tuple = ()) -> dict:
        try:
            connection_object = self.connection_pool.get_connection()

            if connection_object.is_connected():
                cursor = connection_object.cursor(prepared=True)
                cursor.execute(sql, input)
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
            if (connection_object.is_connected()):
                cursor.close()
                connection_object.close()

    def __execute(self, sql: str, input: tuple, insert: bool) -> object:
        try:
            connection_object = self.connection_pool.get_connection()

            if connection_object.is_connected():
                cursor = connection_object.cursor(prepared=True)
                result = cursor.execute(sql, input)
                if insert:
                    return cursor.lastrowid
                else:
                    return result

            else:
                raise Exception("Connection is not connected!")
        except Error as e:
            raise e
        finally:
            if (connection_object.is_connected()):
                cursor.close()
                connection_object.close()

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

    def add_user(self, msisdn, full_name, passwd, team_id):
        sql = "insert into user (msisdn, full_name, passwd, team_id) values (%s,%s,%s,%s);"
        user_id = self.__execute(sql, (msisdn, full_name, hash_password(passwd), team_id), True)
        keys = get_keys()
        sql = "insert into wallet (wallet_key,public_key,private_key,user_id) values (%s,%s,%s,%s);"
        wallet_id = self.__execute(sql, (keys['wallet_key'], keys['public_key'], keys['private_key'], user_id), True)
        return {
            "user_id": user_id,
            "wallet_id": wallet_id
        }

    def delete_user(self, id):
        sql = "delete from user where id = %s"
        return self.__execute(sql, (id,), False)

    def get_users(self, filter="%"):
        return self.__fetchall("select * from user where full_name like '%s'", (filter,))

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
            "SELECT sum(amount) total_sent FROM `transaction` WHERE is_active = 1 and is_succeed = 1 and sender_id = %s",
            (user_id,))
        return result if result else 0

    def get_total_received_transaction(self, user_id):
        result = self.__fetchone(
            "SELECT sum(amount) total_received FROM `transaction` WHERE is_active = 1 and is_succeed = 1 and receiver_id = %s",
            (user_id,))
        return result if result else 0

    def get_lastn_sent(self, user_id, count):
        sql = 'select distinct u.full_name, r.text, date_format(t.transaction_date,"%d %M, %W") date from transaction t, user u, reason r where t.receiver_id = u.id and t.reason_id = r.id and t.is_active = 1 and t.is_succeed = 1 and t.sender_id = %s order by t.transaction_date desc limit %s;'
        return self.__fetchall(sql, (user_id, count))

    def get_lastn_received(self, user_id, count):
        sql = 'select distinct u.full_name, r.text, date_format(t.transaction_date,"%d %M, %W") date from transaction t, user u, reason r where t.sender_id = u.id and t.reason_id = r.id and t.is_active = 1 and t.is_succeed = 1 and t.receiver_id = %s order by t.transaction_date desc limit %s;'
        return self.__fetchall(sql, (user_id, count))
