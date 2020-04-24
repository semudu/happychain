from app.commons.constants.globals import *
from mysql.connector import Error
from app.commons.log import get_logger
from app.commons import database, bip

from app.commons.utils import *
import pyexcel as pe

logger = get_logger(__name__)


def import_user_array(user_array):
    teams = {}
    succeed = []
    failed = []

    for i in range(1, len(user_array)):
        user_fields = user_array[i]
        team_name = user_fields[5]
        if team_name not in teams:
            team_id = database.get_team_id_by_name(team_name)
            if team_id is not None:
                teams[team_name] = team_id

        if team_name in teams:
            try:
                database.add_user(user_fields[0], user_fields[1], user_fields[2], user_fields[3], user_fields[4],
                                  Globals.DEFAULT_PASSWD, teams[team_name])
                succeed.append(user_fields[0])
            except Error as e:
                failed.append({"msisdn": user_fields[0], "description": str(e)})
        else:
            failed.append({"msisdn": user_fields[0], "description": "team[%s] is not found" % team_name})

    return {
        "succeed": succeed,
        "failed": failed
    }


def get_report_file_info(scope_id, scope_name):
    file_name = scope_name + "_Rapor_" + now("%d%m%Y%H%M") + ".xlsx"

    sent_user_list = database.get_sent_user_list_by_scope(scope_id)
    received_user_list = database.get_received_user_list_by_scope(scope_id)
    top_user_list = database.get_top_user_list_by_scope_id(scope_id)
    messages = database.get_messages_by_scope_id(scope_id)

    book = pe.Book(filename=file_name)
    book += pe.Sheet(name="Gönderenler", sheet=sent_user_list)
    book += pe.Sheet(name="Alanlar", sheet=received_user_list)
    book += pe.Sheet(name="Puan Sıralaması", sheet=top_user_list)
    book += pe.Sheet(name="Mesajlar", sheet=messages)
    book.save_as("/tmp/" + file_name)

    try:
        file = open("/tmp/" + file_name, "rb")

        file_url = bip.upload.document(file)
        os.remove("/tmp/" + file_name)

        return {
            "url": file_url,
            "name": file_name[:-5]}

    except Exception as e:
        logger.error(e)
    finally:
        if file is not None:
            file.close()
