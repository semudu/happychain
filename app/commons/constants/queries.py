class SQL:
    # ------------------ SCOPE ------------------ #
    ADD_SCOPE = "insert into scope (name) values (%s);"
    UPDATE_SCOPE = "update scope set name = %s where id = %s;"
    DELETE_SCOPE = "delete from scope where id = %s;"
    GET_SCOPES = "select * from scope;"
    GET_SCOPE_BY_USER_ID = "select s.* from scope s, team t, user u where t.scope_id = s.id and u.team_id = t.id and u.id = %s;"

    # ------------------ TEAM ------------------ #
    ADD_TEAM = "insert into team (name, scope_id) values (%s, %s);"
    UPDATE_TEAM = "update team set name = %s, scope_id = %s where id = %s;"
    DELETE_TEAM = "delete from team where id = %s;"
    GET_TEAMS = "select * from team;"
    GET_TEAM_ID_BY_NAME = "select id from team where name = %s;"

    # ------------------ USER ------------------ #
    ADD_USER = "insert into user (msisdn, first_name, last_name, gender, date_of_birth, passwd, team_id, role) values (%s,upper(%s),upper(%s),%s,%s,%s,%s,%s);"
    GET_USER_BY_ID = "select u.*, concat(u.first_name,' ', u.last_name) as full_name from user u where id = %s;"
    GET_USER_BY_MSISDN = "select u.*, concat(u.first_name,' ', u.last_name) as full_name from user u where msisdn = %s;"
    GET_USER_ID_BY_MSISDN = "select id from user where msisdn = %s;"
    GET_USERS_LIKE_NAME = "select u.*, concat(u.first_name,' ', u.last_name) as full_name from user u where first_name like %s;"
    DELETE_USER = "update user set active = 0 where id = %s;"
    GET_USERS_MSISDN_LIST = "select msisdn from user;"
    GET_BIRTHDAY_USERS = "select u.*, concat(u.first_name,' ', u.last_name) as full_name from user u where dayofmonth(date_of_birth) = dayofmonth(curdate()) and month(date_of_birth) = month(curdate());"
    GET_SCOPE_USERS_BY_USER_ID_AND_LIKE_NAME = "select u.*, concat(u.first_name, ' ', u.last_name) as full_name from user u where u.id != %s and u.team_id in (select id from team where scope_id = (select s.id from scope s, team t, user u where u.team_id = t.id and t.scope_id = s.id and u.id = %s)) and first_name like %s order by full_name limit %s,%s;"
    GET_TOP_TEN_USER_BY_SCOPE = "select *, (t.total_sent * %s + t.total_received * %s ) total from ( select concat(u.first_name, ' ', u.last_name) full_name, (select count(1) from transaction where sender_id = u.id) total_sent, (select count(1) from transaction where receiver_id = u.id) total_received from user u where team_id in (select id from team where scope_id = %s)) t order by total desc limit 10;"

    # ----------------- WALLET ----------------- #
    ADD_WALLET = "insert into wallet (user_id, balance) values (%s,%s);"
    GET_WALLET_BY_USER_ID = "select * from wallet where user_id = %s;"
    GET_BALANCE_BY_USER_ID = "select balance from wallet where user_id = %s;"
    ADD_BALANCE_BY_USER = "update wallet set balance = balance + %s where user_id = %s;"
    REMOVE_BALANCE_BY_USER = "update wallet set balance = balance - %s where user_id = %s;"
    ADD_BALANCE_ALL = "update wallet set balance = balance + %s;"
    UPDATE_BALANCE_ALL = "update wallet set balance = %s;"

    # --------------- TRANSACTION --------------- #
    ADD_TRANSACTION = "insert into transaction (sender_id, receiver_id, amount, date, message_id, free_message, is_active) values (%s,%s,%s,CURRENT_TIMESTAMP(),%s,%s,1);"
    GET_TOTAL_SENT = "SELECT sum(amount) total_sent FROM transaction WHERE is_active = 1 and sender_id = %s;"
    GET_TOTAL_RECEIVED = "SELECT sum(amount) total_received FROM transaction WHERE is_active = 1 and receiver_id = %s;"
    GET_USER_SENT_COUNT_BY_RECEIVER_TODAY = "select count(*) from transaction where sender_id = %s and receiver_id = %s and date = curdate() and is_active = 1;"
    GET_USER_SENT_COUNT_BY_RECEIVER_TEAM_TODAY = "select count(*) from transaction t, user u where t.sender_id = u.id and t.date = curdate() and t.is_active = 1 and t.sender_id = %s and u.team_id = (select team_id from user where id = %s);"
    GET_LAST_N_SENT = "select concat(u.first_name, ' ', u.last_name) as full_name, (case when m.id = -1 then (select free_message ->> '$.content' from transaction where id = t.id) else m.text end) text, date_format(t.date, '%d %M, %W') date from transaction t, user u, message m where t.receiver_id = u.id and t.message_id = m.id and t.is_active = 1 and t.sender_id = %s and (t.id != -1 or (t.id = -1 and t.free_message is not null )) order by t.date desc limit %s;"
    GET_LAST_N_RECEIVED = "select concat(u.first_name, ' ', u.last_name) as full_name, (case when m.id = -1 then (select free_message ->> '$.content' from transaction where id = t.id) else m.text end) text, date_format(t.date, '%d %M, %W') date from transaction t, user u, message m where t.sender_id = u.id and t.message_id = m.id and t.is_active = 1 and t.receiver_id = %s and (t.id != -1 or (t.id = -1 and t.free_message is not null )) order by t.date desc limit %s;"
    GET_LAST_N_RECEIVED_MESSAGES_BY_TEAM = "select u_s.first_name from_first_name, u_s.last_name from_last_name, tm.name from_team, u_r.first_name to_first_name, u_r.last_name to_last_name, (case when t.message_id = -1 then t.free_message ->> '$.content' else m.text end) message, unix_timestamp(t.date) 'timestamp' from transaction t, team tm, user u_r, user u_s, message m where u_s.id = t.sender_id and u_s.team_id = tm.id and t.receiver_id = u_r.id and m.id = t.message_id and u_r.team_id = %s order by t.date desc limit %s;"
    GET_USER_LAST_TRANSACTION_BY_EMPTY_MESSAGE_TODAY = "select * from transaction where sender_id = %s and is_active = 1 and message_id=-1 and free_message is null and date(date) = date(curdate()) order by id desc limit 1;"
    UPDATE_FREE_MESSAGE = "update transaction set free_message = %s where id = %s;"
    ARCHIVE_ACTIVE_TRANSACTIONS = "insert into transaction_archive (date, archive_date, sender_id, receiver_id, message_id, free_message, amount) select date, curdate(), sender_id, receiver_id, message_id, free_message, amount from transaction where is_active = 1;"
    GET_TRANSACTION_COUNT_BY_SCOPE = "select count(*) from transaction t where t.is_active = 1 and sender_id in ( select u.id from user u, team t where u.team_id = t.id and t.scope_id = %s)"
    TRUNCATE_TRANSACTIONS = "truncate table transaction;"

    # --------------- MESSAGE --------------- #
    GET_MESSAGE_BY_ID = "select text from message where id = %s;"
    GET_MESSAGE_LIST_BY_USER_ID = "select r.id, r.text from ( select * from message where direction = 'IN' and type = 'D' and exists(select * from user u where dayofmonth(date_of_birth) = dayofmonth(curdate()) and month(date_of_birth) = month(curdate()) and id = %s) union select * from message where direction = 'IN' and SPLIT_STRING(date, '/', 1) = dayofmonth(curdate()) and SPLIT_STRING(date, '/', 2) = month(curdate()) and (type is null or type = (select gender from user where id = %s)) union select m.* from message m, team t, user u where u.id = %s and u.team_id = t.id and m.direction = 'IN' and (m.type is null or m.type in ('K', 'E')) and m.date is null and ((exists(select * from message where scope_id = t.scope_id) and m.scope_id = t.scope_id) or (not exists(select * from message where scope_id = t.scope_id) and m.scope_id = 0))) r order by r.date desc, r.type desc, r.id asc limit 6;"
    GET_SPECIAL_DATES = "select * from message where direction = 'OUT' and type='S' and scope_id = 0 and split_string(date,'/',1) = dayofmonth(curdate()) and split_string(date,'/',2) = month(curdate());"
    GET_BIRTHDAY_MESSAGE = "SELECT text FROM message where type='D' and scope_id = 0 and direction='OUT'"

    # --------------- REPORT --------------- #
    GET_SENT_USER_LIST_BY_SCOPE_ID = "select concat(u.first_name, ' ', u.last_name) \"Ad Soyad\", tm.name \"Takım\", count(*) \"Toplam Gönderilen\" from transaction t, user u, team tm where t.is_active = 1 and t.sender_id = u.id and u.team_id = tm.id and sender_id in (select u.id from user u, team t where u.team_id = t.id and t.scope_id = %s) group by sender_id order by count(*) desc"
    GET_RECEIVED_USER_LIST_BY_SCOPE_ID = "select concat(u.first_name, ' ', u.last_name) \"Ad Soyad\", tm.name \"Takım\", count(*) \"Toplam Alınan\" from transaction t, user u, team tm where t.is_active = 1 and t.receiver_id = u.id and u.team_id = tm.id and receiver_id in (select u.id from user u, team t where u.team_id = t.id and t.scope_id = %s) group by receiver_id order by count(*) desc"
    GET_TOP_USER_LIST_BY_SCOPE_ID = "select full_name \"Ad Soyad\", team_name \"Takım\", (t.total_sent * %s + t.total_received * %s) \"Kazanılan\" from (select concat(u.first_name, ' ', u.last_name) full_name, t.name team_name, (select count(1) from transaction where sender_id = u.id) total_sent, (select count(1) from transaction where receiver_id = u.id) total_received from user u, team t where u.team_id = t.id and t.scope_id = %s) t order by (t.total_sent * %s + t.total_received * %s) desc"