import threading

from app.commons.constants.globals import *
from app.commons.constants.task import Task
from mysql.connector import Error
from app.commons.log import get_logger
from .database import Database

logger = get_logger(__name__)


class Service:
    def __init__(self):
        self.db = Database()
        self.task = Task()

    def import_user_array(self, user_array):
        teams = {}
        succeed = []
        failed = []

        for i in range(1, len(user_array)):
            user_fields = user_array[i]
            team_name = user_fields[5]
            if team_name not in teams:
                team_id = self.db.get_team_id_by_name(team_name)
                if team_id is not None:
                    teams[team_name] = team_id

            if team_name in teams:
                try:
                    self.db.add_user(user_fields[0], user_fields[1], user_fields[2], user_fields[3], user_fields[4],
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

    def process_command(self, request_json):
        t = threading.Thread(target=self.task.run, args=(request_json,))
        t.start()
